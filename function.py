import asyncio
import aiohttp
import requests
import re
import browser_cookie3
import concurrent.futures
import queue
from fake_useragent import UserAgent as UA
from json import load
from tqdm import tqdm
from time import sleep
from random import uniform
from os import path,remove
from sys import _getframe

ProxyPool_url = 'http://101.42.41.111:5555/random' #获取随机IP代理的地址
# cookie_jar
cookie_jar_all = browser_cookie3.load() 

ua_global = UA(verify_ssl=False)

def get_random_proxy():
    """
    get random proxy from proxypool
    :return: proxy
    """
    proxies = None
    if ProxyPool_url != "":
        try:
            proxy = requests.get(ProxyPool_url).text.strip()
            proxies = {
                'http': 'http://' + proxy,
            }
        except Exception:
            proxies = None
    return proxies

def retry(max_retries=3, sleep_duration=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception:
                    if i < max_retries - 1:
                        print(f"Retrying after {sleep_duration} seconds...")
                        sleep(sleep_duration)
                    else:
                        print("Max retries exceeded. Aborting.")
                        raise
        return wrapper
    return decorator

def load_config():
    ckey_url = 'https://g.alicdn.com/player/beta-ykplayer/2.1.76/youku-player.min.js'
    ckey_req = requests.get(url=ckey_url)
    re_bds_ckey = '(?=this.*?)this\.uabModule\.getUA\(\):"([A-Za-z0-9/\+]*)"}'
    pattern = re.compile(re_bds_ckey,re.S)
    tudou_ckey = pattern.findall(ckey_req.text)[0]
    with open("./config/config.json", "r", encoding='utf-8') as f:
        config_dict = load(f)
    return config_dict,tudou_ckey

def sort_order(d):
    return int(d['start'])

def get_from_url(url,web_id,video_id,func_name,params = None, stream = True, expect = None,use_proxy = False):
        
        cj = cookie_jar_all
        for _ in range(3):
            headers = {'User-Agent': ua_global.random}
            if use_proxy:
                proxies = get_random_proxy()
                print(f'using proxies:{proxies}')
            else:
                proxies = None
            res = requests.get(url=url, headers=headers, stream = stream, params=params,proxies=proxies,cookies=cj)
            if res.status_code == 200:
                break
            else:
                print(f'\033[35m{web_id}{video_id}:get failed with code {res.status_code}, retrying...\033[0m')
                sleep(uniform(0.5, 1.5))
        
        if res.status_code != 200:
            print(f'\033[31m{web_id}:{video_id} get failed with code {res.status_code} in {func_name}, aborting...\033[0m')
            if expect is None:
                return None
            else:
                raise expect
        
        return res

# 简单的单线程同步下载器
def single_downloader(filename,desc,url, mode='wb',use_proxy = False):
    '''
        单线程下载器
    '''
    #增加返回code检查，如果返回code不是200，就不下载，直接返回
    file = get_from_url(url,_getframe().f_code.co_name,expect = RuntimeError("download failed."),use_proxy=use_proxy)
    if file is None:
        return True
    
    # 去除文件名中的空格及竖线
    filename = filename.replace(" ","")
    filename = filename.replace("|","_")
    path.exists(filename) and remove(filename)
    with open(filename, mode) as f,tqdm(desc = desc,total = int(file.headers['content-length']),unit = 'iB',
        unit_scale = True,unit_divisor = 1024,leave= False,
    ) as bar:
        for chunk in file.iter_content(chunk_size=1024):
            if chunk:
                size = f.write(chunk)
                bar.update(size)
    return False

# 协程下载器
async def async_downloader(url,filename,desc,web_id,video_id,sem = asyncio.Semaphore(8)):
    '''
        协程下载器
    '''
    headers = {'User-Agent': ua_global.random}
    async with sem:
        async with aiohttp.ClientSession(headers=headers) as session:
            for i in range(3):
                try:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            print(f'\033[31m{web_id}:{video_id} download failed with {resp.status}, retry...\033[0m')
                            continue
                        length = int(resp.headers['content-length'])
                        with open(filename,'wb') as f,tqdm(desc = desc,total = length,unit = 'iB',
                            unit_scale = True,unit_divisor = 1024,leave= False,
                        ) as bar:
                            while True:
                                chunk = await resp.content.read(1024*1024)
                                if not chunk:
                                    break
                                size = f.write(chunk)
                                bar.update(size)
                    break
                except Exception as e:
                    if i ==2 :
                        print(f'\033[31m{web_id}:{video_id} download failed with {e}, aborting...\033[0m')
                        break

#协程分片下载器
async def download_part(url, start, end, semaphore):
    
    async with semaphore:
        headers = {'Range': 'bytes={}-{}'.format(start, end)}
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as resp:
                    if resp.status == 206:
                        content = await resp.read()
                        return content
        except Exception as e:
            print(e)
            return content

async def async_downloader_clip(url,filename,web_id,video_id,chunks_num = 4):
    '''
        协程分片下载器
    '''
    async with aiohttp.ClientSession() as session:
        for i in range(3):
            try:
                async with session.get(url) as resp:
                    length = int(resp.headers['content-length'])
                    chunk_size = length // chunks_num
                    starts = [x * chunk_size for x in range(chunks_num)]
                    ends = [(x + 1) * chunk_size for x in range(chunks_num)]
                    ends[-1] = length - 1
                    tasks = []
                    semaphore = asyncio.Semaphore(4)
                    for i in range(chunks_num):
                        task = asyncio.ensure_future(download_part(url, starts[i], ends[i], semaphore))
                        tasks.append(task)

                    results = await asyncio.gather(*tasks)
                    with open(filename, 'wb') as f:
                        for result in results:
                            f.write(result)   
                break
            except Exception as e:
                if i ==2 :
                    print(f'\033[31m{web_id}:{video_id} download failed with {e}, aborting...\033[0m')
                    break


#多线程下载器
def _multi_thread_downloader(q: queue.Queue,web_id,video_id,use_proxy = False):
    headers= {'User-Agent': ua_global.random}
    while not q.empty():
        url,filename = q.get()
        for i in range(3):
            try:
                desc = f'Downloading {filename}'
                if use_proxy:
                    proxies = get_random_proxy()
                    print(f'using proxies:{proxies}')
                else:
                    proxies = None
                r = requests.get(url,headers=headers,cookies=cookie_jar_all,stream=True,proxies=proxies)
                if r.status_code != 200:
                    print(f'\033[31m{web_id}: {video_id} download failed with {r.status_code}, aborting...\033[0m')
                    break
                length = int(r.headers['content-length'])
                with open(filename,'wb') as f,tqdm(desc = desc,total = length,unit = 'iB',
                    unit_scale = True,unit_divisor = 1024,leave= False,
                ) as bar:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            size = f.write(chunk)
                            bar.update(size)
                break
            except Exception as e:
                if i ==2 :
                    print(f'\033[31m{web_id}:{video_id} download failed with {e}, aborting...\033[0m')
                    break
        
        q.task_done()

def multi_thread_downloader(url_list:list,web_id:str,video_id:str,file_name_list:list,use_proxy:bool=False):
    '''
        多线程下载器
    '''
    q = queue.Queue()
    for i in range(len(url_list)):
        q.put((url_list[i],file_name_list[i]))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_multi_thread_downloader, q,web_id,video_id,use_proxy) for _ in range(4)]
        
        q.join()

        # 取消所有线程
        for future in futures:
            future.cancel()

def _multi_thread_downloader_clip(url,start, end,web_id,video_id,use_proxy):
    headers = {'Range': 'bytes={}-{}'.format(start, end)}
    for _ in range(3):
        try:
            if use_proxy:
                proxies = get_random_proxy()
                print(f'using proxies:{proxies}')
            else:
                proxies = None
            r = requests.get(url,headers=headers,cookies=cookie_jar_all,stream =True,proxies=proxies)
            if r.status_code == 206:
                desc = f'Downloading {web_id}:{video_id}: {start} - {end}'
                length = int(r.headers['content-length'])
                content = b''
                with tqdm(desc = desc,total = length,unit = 'iB',
                            unit_scale = True,unit_divisor = 1024,leave= False,
                        ) as bar:
                            for chunk in r.iter_content(chunk_size=1024*1024):
                                if chunk:
                                    size = len(chunk)
                                    content += chunk
                                    bar.update(size)
                return {'start':start,'content':content}
            else:
                print(f'\033[31m{web_id}: {video_id} download failed with {r.status_code}, retry...\033[0m')
                
        except Exception as e:
            print(f'\033[31m{web_id}:{video_id} download failed with {e}, aborting...\033[0m')
            
    return {'start':start,'content':b''}

def multi_thread_downloader_clip(url,web_id:str,video_id:str,file_name,use_proxy = False,chunks_num = 4):
    '''
        多线程分片下载器
    '''
    headers = {'User-Agent': ua_global.random}
    resp = requests.head(url,headers=headers,cookies=cookie_jar_all)
    length = int(resp.headers['content-length'])
    chunk_size = length // chunks_num
    starts = [x * chunk_size for x in range(chunks_num)]
    ends = [(x + 1) * chunk_size for x in range(chunks_num)]
    ends[-1] = length - 1
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_multi_thread_downloader_clip, url,starts[i],ends[i],web_id,video_id,use_proxy) for i in range(chunks_num)]

    for future in concurrent.futures.as_completed(futures):
        results.append(future.result())

    results = sorted(results,key=sort_order)
    
    with open(file_name, 'wb') as f:
        for result in results:
            f.write(result['content'])
    # 取消所有线程
    for future in futures:
        future.cancel()