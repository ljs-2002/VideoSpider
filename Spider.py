import requests
import csv
import re
import asyncio
import platform
from sys import _getframe
from multiprocess import Pool, Manager, freeze_support
from shutil import rmtree
from pandas.io.excel import ExcelWriter
from pandas import read_csv
from os import path, makedirs, system
from time import sleep, time
from random import uniform
from copy import deepcopy
from json import load,dump
from lxml import etree
from WebClass import WebDict
from function import get_from_url,single_downloader,async_downloader,multi_thread_downloader,multi_thread_downloader_clip

task_order = ['tudou','haokan','v','ku6','ifeng','thepaper','cctv']

def sort_order(d):
    return task_order.index(d['web_id'])

# 每个网站有四个属性，id, 基础url，params，解析的xpath, 以及对应的函数
# 其中xpath 包含5个值：标题，简介，播放量,热力值,点赞数

fail_list = []

class VideoSpider(object):
    def __init__(self,task_file:str ='./config/VideoList.json',
                 output_file:str ='VideoList.csv',
                 output_dir:str ='./output',
                 video_list: list = [],
                 to_excel:bool = False,
                 gui_mod:bool = False,) -> None:
        self.task_file = task_file
        self.output_file = output_file
        self.output_dir = output_dir
        self.output_path = path.join(self.output_dir, self.output_file)
        self.to_excel = to_excel
        self.search_mod = False
        self.search_keywords = ''
        self.gui_mod = gui_mod
        self.video_list = video_list
        self.url = ''
        self.xpath = {}
        self.web_id = ''
        self.video_id = ''
        self.video_title = ''
        self.like_url_func = None
        self.view_url_func = None
        self.file_url_func = None
        self.ts_url_func = None
        self.get_search_list_func = None
        self.fail_list = []
        
        self.fail_log = path.join(self.output_dir, 'fail_log')
        self.fieldNames = ['web_id','video_id','title', 'intro', 'hot', 'like', 'view']

    def get_html_request(self,url,params):
        res = get_from_url(url, self.web_id,self.video_id,_getframe().f_code.co_name, params=params,expect = RuntimeError)
        html = res.content.decode('utf-8')
        self.parse_html_xpath(html,self.xpath)

    def get_and_prase(self, url, re_bds):
        res = get_from_url(url,self.web_id,self.video_id,_getframe().f_code.co_name)
        if res is None:
            return None
        html = res.text
        pattern = re.compile(re_bds, re.S)
        return pattern.findall(html)[0]


    def hls_download(self,url,dir_path,filename): 
        ts_list = self.ts_url_func(url=url)
        num_list = [str(i).zfill(8) for i in range(len(ts_list))]
        name_dict = dict(zip(ts_list,num_list))
        path.exists(dir_path) and rmtree(dir_path)
        makedirs(dir_path)
        print('downloading ts file...')
        
        if self.web_id != 'tudou':
            loop = asyncio.get_event_loop()
            task = [async_downloader(ts,dir_path+name_dict[ts]+'.ts','Downloading '+self.web_id+self.video_id+'_'+name_dict[ts],self.web_id,self.video_id) for ts in ts_list]
            print('start async download')
            loop.run_until_complete(asyncio.wait(task))
        else:
            # for ts in ts_list:
            #     self.download(dir_path+name_dict[ts]+'.ts','Downloading '+self.web_id+self.video_id+'_'+name_dict[ts],ts,stream = True)
            file_name_list = []
            
            for ts in ts_list:
                file_name_list.append(dir_path+name_dict[ts]+'.ts')
            print('start multi thread download')
            multi_thread_downloader(ts_list,self.web_id,self.video_id,file_name_list)
            
        print('done.')
        print('Merging ts file...')
        # 使用ffmpeg合并ts文件为MP4
        file_list = [dir_path+name_dict[ts]+'.ts' for ts in ts_list]
        file_string = '|'.join(file_list)
        
        cmd = f'ffmpeg -i "concat:{file_string}" -c copy "{filename}" -y -loglevel quiet'
        system(cmd)
        # 删除ts文件
        rmtree(dir_path)
        print('done.')

    def get_file(self, html,video_title):

        url = self.file_url_func(html=html,video_id = self.video_id)
        if 'm3u8' in url:
            path = './file/HLS/'+self.web_id+self.video_id+'/'
            filename = './file/HLS/'+self.web_id + self.video_id + video_title[:10] + '.mp4'
            # 删除特殊字符
            filename = re.sub(r'[\\:*?"<>| | ：]', '', filename)
            self.hls_download(url,path,filename)
        else:
            desc = 'Downloading '+self.web_id+self.video_id
            filename = './file/MP4/'+self.web_id + self.video_id + video_title[:15] + '.mp4'
            filename.strip()
            filename = re.sub(r'[\\:*?"<>| | ：，。：“’‘”]', '', filename)
            print('downloading MP4 file...')
            head = requests.head(url)
            head = head.headers
            # 使用异步协程和多线程下载效率类似，但异步协程在Windows下会有报错，虽然不影响程序的运行，但是有碍观感
            if head['Accept-Ranges']=='bytes':
                multi_thread_downloader_clip(url,self.web_id,self.video_id,filename,self.use_proxy)
                # loop = asyncio.get_event_loop()
                # task=[async_downloader_clip(url,filename,self.web_id,self.video_id)]
                # loop.run_until_complete(asyncio.wait(task))
            else:
                single_downloader(filename, desc, url,use_proxy=self.use_proxy)
            print('done.')

    def parse_html_xpath(self, html,xpath):
        parse_html = etree.HTML(html)
        xpath_title = xpath['title']
        xpath_intro = xpath['intro']
        xpath_hot = xpath['hot']
        xpath_like = xpath['like']
        xpath_view = xpath['view']
        item = {}

        item['web_id'] = self.web_id
        item['video_id'] = self.video_id


        try:
            if self.web_id == 'ku6':
                pattern = re.compile(xpath_title, re.S)
                item['title'] = pattern.findall(html)[0]
            else:
                item['title'] = parse_html.xpath(xpath_title)[0]

            if xpath_intro != '':
                intro = parse_html.xpath(xpath_intro)
                item['intro'] = intro[0] if len(intro)>0 else 'None'
            else:
                item['intro'] = 'None'

            if xpath_hot != '':
                item['hot'] = parse_html.xpath(xpath_hot)[0].replace("\n", "")
            else:
                item['hot'] = 'None'

            if self.like_url_func is not None:
                url = self.like_url_func(html=html, video_id=self.video_id)
                like = self.get_and_prase(url, xpath_like)
                item['like'] = like
            elif xpath_like != '':
                item['like'] = parse_html.xpath(xpath_like)[0].replace("\n", "")
            else:
                item['like'] = 'None'

            if self.view_url_func is not None:
                url = self.view_url_func(html=html, video_id=self.video_id)
                view = self.get_and_prase(url, xpath_view)
                item['view'] = view
            elif xpath_view != '':
                re_bds = r'(\d+\.?\d*)次播放'
                view = parse_html.xpath(xpath_view)[0].replace("\n", "")
                pattern = re.compile(re_bds, re.S)
                item['view'] =  pattern.findall(view)[0]
            else:
                item['view'] = 'None'
            item['title'] = item['title'].replace("\n", "")
        except Exception as e:
            print(e)
            raise e('prase video info failed')
        video_title = item['title']
        print('get video info down')
        try:
            self.get_file(html,video_title)
        except Exception as e:
            print("get video file failed with error: ",e)
        self.save_html_xpath(item)

    def save_html_xpath(self, item_dict):
        path.exists(self.output_dir) or makedirs(self.output_dir)
        out = self.output_path
        if self.multi_process:
            self.csv_lock.acquire()
        
        with open(out, 'a', newline="", encoding='utf-8') as f:
            
            writer = csv.DictWriter(f, fieldnames=self.fieldNames)
            try:
                writer.writerow(item_dict)
            except Exception as e:
                print(e)
        if self.multi_process:
            self.csv_lock.release()
    
    def save_to_excel(self):
        #将csv文件转换为excel文件
        xls = path.join(self.output_dir, 'output.xlsx')
        with ExcelWriter(xls) as ew:
            read_csv(self.output_path).to_excel(ew, sheet_name="1", index=False)

    def get_video_list(self):
        # web_id,video_id
        with open(self.task_file, "r") as f:
            video_list = load(f)
        return video_list

    def search_by_keyword(self, keyword_list:list, gui_mod:bool=False):

        if self.gui_mod == False and gui_mod == False:
            kw_list = self.search_keywords.split(sep="_")
        else:
            kw_list = keyword_list

        result = []

        for kw in kw_list:
            web_id,keyword = kw.split(sep=":")
            # 1. 根据搜索的url和关键词请求搜索结果页面
            # 来自Web()的search_url_list_func
            search = WebDict[web_id].default_get_search
            if search is None:
                print(f'{web_id} has no search function')
                continue
            video_list = search(keyword=keyword)
            
            # 2. 将解析出的url选取前10个添加到VideoList.json中，如果已经存在则不添加
            if len(video_list)>10:
                video_list = video_list[:10]
            
            key = ["web_id","video_id"]
            web_video = [[web_id,video_list[i]] for i in range (len(video_list))]
            result.extend(web_video)
            new_dict_list = [dict(zip(key,web_video[i])) for i in range(len(video_list))]
            
            if self.gui_mod or gui_mod:
                continue
            else:
                if path.exists(self.task_file) and path.getsize(self.task_file)>0:
                    with open(self.task_file, "r") as f:
                        dict_list = load(f)
                    
                    for item in new_dict_list:
                        if item not in dict_list:
                            dict_list.append(item)
                else:
                    dict_list = new_dict_list

                with open(self.task_file, "w") as f:
                    dump(dict_list,f)
            
        return result

    
    def launch(self,video=[{}]):
        success = False
        global fail_list
        while True:
            if self.multi_process:
                if self.task_Queue.empty():
                    break
                video = self.task_Queue.get()
            Web = deepcopy(WebDict[video['web_id']])
            Web.id = video['video_id']
            self.web_id = video['web_id']
            self.video_id = video['video_id']
            self.url, self.xpath = Web.get_ux()
            self.file_url_func, self.ts_url_func = Web.default_get_file, Web.default_get_ts
            self.like_url_func, self.view_url_func = Web.default_get_like, Web.default_get_view
            sleep_time = 0.5
            params = Web.get_params(id=video['video_id'])
            for retry_time in range(3):
                try:
                    # 开始爬虫
                    self.get_html_request(self.url,params)
                except Exception as e:
                    print("\033[36m{0}:{1}:错误：{2}\033[0m".format(video['web_id'], video['video_id'],e))
                    if(retry_time < 2):
                        print("\033[34m{0}:{1}: {2}s后重试...\033[0m".format(video['web_id'], video['video_id'],sleep_time))
                        sleep(sleep_time)
                        sleep_time *=2
                    else:
                        print("\033[44m{0}:{1}:重试次数超过限制，跳过\033[0m".format(video['web_id'], video['video_id']))
                        #加入失败列表
                        if self.multi_process:
                            self.fail_list_lock.acquire()
                            self.fail_list.append(video)
                            print('previous fail list length:',len(self.fail_list))
                            self.fail_list_lock.release()
                        else:
                            fail_list.append(video)
                            print('previous fail list length:',len(fail_list))
                            success = False
                    continue
                success = True
                break
                
            del (Web)
            if success :
                print("{0}:{1} down".format(video['web_id'], video['video_id']))
            
            if not self.multi_process or self.task_Queue.empty():
                break
            
        return success

    def run(self,task_file:str ='./config/VideoList.json',
                 output_file:str ='output.csv',
                 output_dir:str ='./output',
                 video_list: list = [],
                 to_excel:bool = False,
                 gui_mod:bool = False,
                 search_mod:bool = False,
                 search_keywords:str = '',
                 multi_process:bool = False,
                 use_proxy:bool = False):
        
        self.task_file = task_file
        self.output_file = output_file
        self.output_dir = output_dir
        self.to_excel = to_excel
        self.gui_mod = gui_mod
        self.video_list = video_list
        self.multi_process = multi_process
        self.search_mod=search_mod
        self.search_keywords = search_keywords
        self.use_proxy = use_proxy
        global fail_list
        fail_list.clear()

        print('check path...')
        self.output_path = path.join(self.output_dir, self.output_file)
        path.exists(self.output_dir) or makedirs(self.output_dir)
        # 创建储存视频的文件夹
        
        path.exists('./file') or makedirs('./file')
        path.exists('./file/MP4') or makedirs('./file/MP4')
        path.exists('./file/HLS') or makedirs('./file/HLS')
        # 检查csv文件是否具有标题行，若没有则添加
        path.exists(self.output_path) or open(self.output_path, 'w', newline="", encoding='utf-8').close()
        with open(self.output_path, 'r+', newline="", encoding='utf-8') as f:
            reader = csv.reader(f)
            if not next(reader, None):
                writer = csv.DictWriter(f, fieldnames=self.fieldNames)
                writer.writeheader()
        
        print("get task list...")
        # 读取视频任务列表
        if self.search_mod:
            self.search_by_keyword(self.search_keywords)
        
        if not self.gui_mod :
            video_list = self.get_video_list()
        else:
            #从前端获取视频任务列表，并写入到任务文件中
            video_list = self.video_list
        
        task_size = len(video_list)
        print("task amount: ",task_size,flush=True)
        
        video_list.sort(key = sort_order)
        # 多进程
        if self.multi_process:
            if platform.system() == 'Windows':
                print("\033[32mfreeze_support...",flush=True)
                freeze_support()
            else:
                print('\033[32m',flush = True)
            manager = Manager()
            print("create share Queue...",flush=True)
            self.task_Queue = manager.Queue(len(video_list))
            print("create share list...",flush=True)
            self.fail_list = manager.list()
            print("create share csv_lock...",flush=True)
            self.csv_lock = manager.Lock()
            print("create share fail_list lock...\033[0m",flush=True)
            self.fail_list_lock = manager.Lock()
            print("insert queue...",flush=True)
            for task in video_list:
                self.task_Queue.put(task)

            result_list = []
            
            print("start multi process...",flush=True)

            p = Pool(processes=4)
            time_start = time()
            for _ in range(4):
                ret = p.apply_async(self.launch, args=())
                result_list.append(ret)

            p.close() # 关闭进程池
            p.join() # 阻塞主进程，等待子进程全部执行完毕
            for ret in result_list:
                ret.get()
            time_end = time()
            print("\033[32mtotal success task: ",str(task_size-len(self.fail_list))," Multi_process mod time usage: ",time_end-time_start,"\033[0m",flush=True)
            if len(self.fail_list)> 0:
                fail_list = list(self.fail_list)
            manager.shutdown()
        # 单进程
        else:
            time_start = time()
            for video in video_list:
                self.launch(video)
                #sleep(uniform(0.5, 1))
            time_end = time()
            print("\033[32mtotal success task: ",str(task_size-len(fail_list))," Single Process mod time usage: ",time_end-time_start,"\033[0m",flush=True)

        # 显示和保存失败列表
        if len(fail_list)> 0:
            print("\033[33mfail list: ",fail_list)
            print("\033[0m")
            with open(self.fail_log+f"_{str(time()*1000)}.json", "w") as f:
                dump(fail_list,f)
            fail_list.clear()

        # 保存到excel
        if self.to_excel:
            self.save_to_excel()