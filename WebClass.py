from json import load,dumps
from time import time,sleep
from fake_useragent import UserAgent as UA
from random import choice
import re
import requests
from urllib import parse
from hashlib import md5

WebDict = {}

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

class WebSiteInfo():
    def __init__(self, get_url=None, get_param=None, get_view=None, get_like=None, get_file=None, get_ts=None,get_search=None) -> None:
        self.url = ''
        self.params = {}
        self.xpath = {}
        self.id = ''
        self.default_get_url = get_url
        self.default_get_params = get_param
        self.default_get_view = get_view
        self.default_get_like = get_like
        self.default_get_file = get_file
        self.default_get_ts = get_ts
        self.default_get_search = get_search

    def get_params(self, **kwarg) -> dict:
        if self.default_get_params is None:
            return self.params
        else:
            return self.default_get_params(**kwarg)

    def set_ux(self, config_dict) -> None:
        self.url = config_dict['url']
        self.xpath.clear()
        self.xpath.update(config_dict['xpath'])

    def get_ux(self):
        url = self.url
        if self.default_get_url is not None:
            url = self.default_get_url(id=self.id, url=self.url)
        return url, self.xpath

    def get_view(self,**kwarg):
        if self.default_get_view is not None:
            return self.default_get_view(**kwarg)
        else:
            return 'None'
    
    def get_like(self,**kwarg):
        if self.default_get_like is not None:
            return self.default_get_like(**kwarg)
        else:
            return 'None'
        
def load_config():
    with open("./config/config.json", "r", encoding='utf-8') as f:
        config_dict = load(f)
    return config_dict

config_dict = load_config()

def get_url_v(**kwarg):
    id = kwarg['id']
    url = kwarg['url']
    re = url+id+'.html'
    return re

def get_file_v_url(**kwarg):
    html = kwarg['html']
    re_bds = '[0-9_]*\.mp4'
    pattern = re.compile(re_bds,re.S)
    url_list = pattern.findall(html)
    url = 'https://pgcvideo-cdn.xiaodutv.com/'+url_list[0]
    return url

def get_params_haokan(**kwarg):
    id = kwarg['id']
    params = {
        'vid': str(id)
    }
    return params

def get_file_haokan_url(**kwarg):
    html = kwarg['html']
    html = html.replace('\\','')
    html = re.sub('[\u4e00-\u9fa5]', '', html)
    re_bds = '(?="playurl":)"playurl":"(https://vd[0-9].bdstatic.com/.*?mp4)'
    pattern = re.compile(re_bds,re.S)
    url_list = pattern.findall(html)
    url = url_list[0]

    return url


@retry(max_retries=3, sleep_duration=1)
def get_search_haokan_list(**kwarg):
    keyword = kwarg["keyword"]
    kw = parse.quote(keyword)
    timestamp = str(int(time()*1000))
    string = "1_{}_10_{}_1".format(kw, timestamp)
    md = md5(string.encode()).hexdigest()
    params={
                'pn':'1',
                'rn': '10',
                'type':'video',
                'version':'1',
                'sign': md,
                'query': keyword,
                'timestamp': timestamp
            }
    ua = UA()
    ref = 'https://haokan.baidu.com/web/search/page?query={}&sfrom=recommend'.format(kw)
    cookie ='BDUSS=VTWFZ1VERneElZfkRZS3FkWWktdmFRYzktNWs4RHNDdU1vWXllZ3JPU0hBRTFqRVFBQUFBJCQAAAAAAAAAAAEAAABkzhj6ztLO3sTjw~vQodfkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIdzJWOHcyVjdk'
    headers = {'User-Agent': ua.random, 'Referer':ref, 'Cookie':cookie}
    req = requests.get(url='https://haokan.baidu.com/haokan/ui-search/pc/search/video?',params=params,headers=headers)
    req_json = req.json()
    url_list = req_json['data']['list']
    vid_list = [url_list[i]['vid'] for i in range(len(url_list))]
    return vid_list

def get_params_ku6(**kwarg):
    id = kwarg['id']
    params = {
        'id': str(id)
    }
    return params

def get_url_ku6(**kwarg):
    id = kwarg['id']
    url = kwarg['url']
    re = url+id+'.'
    return re

def get_file_ku6_url(**kwarg):
    html = kwarg['html']
    re_bds = 'flvURL: "(.*?)"'
    pattern = re.compile(re_bds,re.S)
    url_list = pattern.findall(html)
    url = url_list[0]
    return url

def get_url_ifeng(**kwarg):
    id = kwarg['id']
    url = kwarg['url']
    re = url+id
    return re

def get_like_ifeng_url(**kwarg):
    html = kwarg['html']
    id = kwarg['video_id']
    url = 'https://survey.news.ifeng.com/api/getaccumulatorweight?key='
    re_bds = '(?="base62Id.*?)"base62Id":"'+str(id)+'","guid":"(.*?)"'
    pattern = re.compile(re_bds,re.S)
    key = pattern.findall(html)[0]
    url = url + key + 'ding&format=js&serviceid=1&callback=getVideoZan_0'
    return url

def get_view_ifeng_url(**kwarg):
    html = kwarg['html']
    id = kwarg['video_id']
    url = ' https://survey.news.ifeng.com/api/getaccumulatorweight?key[]='
    re_bds = '"base62Id":"'+str(id)+'","guid":"(.*?)"'
    pattern = re.compile(re_bds,re.S)
    key = pattern.findall(html)[0]
    url = url + key + '&&format=js&serviceid=1&callback=getVideoComment1'
    return url

def get_file_ifeng_url(**kwarg):
    html = kwarg['html']
    re_bds = '"videoPlayUrl":"(.*?.mp4)'
    pattern = re.compile(re_bds,re.S)
    url_list = pattern.findall(html)
    url = url_list[-1]
    return url

def get_like_thepaper_url(**kwarg):
    id = kwarg['video_id']
    url = 'https://api.thepaper.cn/contentapi/article/detail/interaction/state?contId='
    res = url+str(id)
    return res

def get_url_thepaper(**kwarg):
    id = kwarg['id']
    url = kwarg['url']
    res = url+id
    return res

def get_file_thepaper_url(**kwarg):
    html = kwarg['html']
    re_bds = 'https://cloudvideo.thepaper.cn/video/.*?\\.mp4'
    pattern = re.compile(re_bds,re.S)
    url = pattern.findall(html)[0]
    return url

@retry(max_retries=3, sleep_duration=1)
def get_search_thepaper_list(**kwarg):
    keyword = kwarg['keyword']
    contentType = 'application/json'
    video_author = ['七环视频','温度计','一级视场','World湃','湃客科技','记录湃','奇客解','围观','@所有人','大都会','追光灯','运动装','健寻记','AI播报','眼界','关键帧']
    ua = UA(verify_ssl=False)
    url = 'https://api.thepaper.cn/search/web/news'
    headers = {
        'User-Agent': ua.random,
        "Content-Type": contentType
    }
    video_id_list=[]
    pageNum=1
    while len(video_id_list)< 10:
        payload = {
            'orderType': '3',
            'pageNum': str(pageNum),
            'pageSize': '30',
            'searchType': '1',
            'word': keyword
        }
        req = requests.post(url=url,headers=headers,data=dumps(payload))
        res_json = req.json()
        item_list = res_json['data']['list']
        for item in item_list:
            if item['nodeInfo']['name'] in video_author:
                video_id_list.append(item['objectInfo']['object_id'])
        
        pageNum+=1
    
    return video_id_list


def get_url_tudou(**kwarg):
    id = kwarg['id']
    url = kwarg['url']
    res = url+id+'==.html'
    return res

@retry(max_retries=3, sleep_duration=1)
def get_file_tudou_url(**kwarg):
    # HLS
    id = kwarg['video_id']
    timemap = int(time())
    ccode_list = ['0562','0564','0566','0568']
    url = 'https://ups.youku.com/ups/get.json?vid=XNTk'+id+'==&ccode='+choice(ccode_list)+'&client_ip=192.168.1.1&client_ts='+str(timemap)+'&utid=oEQIGJ3tKmkCAXty8yEG6ff/&ckey=DIl58SLFxFNndSV1GFNnMQVYkx1PP5tKe1siZu/86PR1u/Wh1Ptd+WOZsHHWxysSfAOhNJpdVWsdVJNsfJ8Sxd8WKVvNfAS8aS8fAOzYARzPyPc3JvtnPHjTdKfESTdnuTW6ZPvk2pNDh4uFzotgdMEFkzQ5wZVXl2Pf1/Y6hLK0OnCNxBj3+nb0v72gZ6b0td+WOZsHHWxysSo/0y9D2K42SaB8Y/+aD2K42SaB8Y/+ahU+WOZsHcrxysooUeND'
    ua = UA(verify_ssl=False)
    headers = {'User-Agent': ua.random,'cookie':'cna=oEQIGJ3tKmkCAXty8yEG6ff/; _m_h5_tk=34dde030b19bc02e51e9bb3add339bb8_1680074627374; _m_h5_tk_enc=15485aba829f4257b77b8b363315ee36'}
    resq = requests.get(url=url,headers=headers)
    resq_json = resq.json()
    m3u8_url_list = resq_json['data']['stream']
    for m3u8_url in m3u8_url_list:
        if m3u8_url['stream_type'] == 'mp4hd':
            m3u8_url = m3u8_url['m3u8_url']
            break
    return m3u8_url

@retry(max_retries=3, sleep_duration=1)
def get_ts_tudou_url(**kwarg):
    url = kwarg['url']
    ua = UA(verify_ssl=False)
    headers = {'User-Agent': ua.random}
    req_m3u8 = requests.get(url=url,headers=headers)
    m3u8 = req_m3u8.text
    pattern = re.compile('(http.*?)[\r\n ]*?#', re.S)
    ts_list = pattern.findall(m3u8)
    return ts_list

def get_url_cctv(**kwarg):
    id = kwarg['id']
    url = kwarg['url']
    length = len(id)
    data = id[length-6:]
    url = url+'20'+data[:2]+'/'+data[2:4]+'/'+data[4:]+'/VIDE'+id+'.shtml'
    return url

def get_like_cctv_url(**kwarg):
    id = kwarg['video_id']
    timemap = int(time())
    url = 'https://common.itv.cntv.cn/praise/get?type=other&id=VIDE'+id+'&r='+str(timemap)
    res = url+str(id)
    return res

@retry(max_retries=3, sleep_duration=1)
def get_file_cctv_url(**kwarg):
    html = kwarg['html']
    re_bds = 'guid[ ]=[ ]"(.*?)";'
    pattern = re.compile(re_bds,re.S)
    guid = pattern.findall(html)[0]
    ua = UA(verify_ssl=False)
    headers = {'User-Agent': ua.random}
    video_info_url = 'https://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid='+guid
    resq_video_info = requests.get(url=video_info_url,headers=headers)
    resq_video_info_json = resq_video_info.json()
    main_m3u8_url = resq_video_info_json['hls_url']
    resq_main_m3u8 = requests.get(url=main_m3u8_url,headers=headers).text
    # 默认获取1280x720
    re_bds = '(/[^#]*?1200\.m3u8)'
    re_bds2 = '.*?com'
    pattern = re.compile(re_bds,re.S)
    pattern2 = re.compile(re_bds2,re.S)
    url_list = pattern.findall(resq_main_m3u8)
    url_pre = pattern2.findall(main_m3u8_url)[0]
    url = url_pre+url_list[0]
    return url

@retry(max_retries=3, sleep_duration=1)
def get_ts_cctv_url(**kwarg): 
    url = kwarg['url']
    ua = UA(verify_ssl=False)
    headers = {'User-Agent': ua.random,
               'Referer': 'https://v.cctv.com/',
               'Origin': 'https://v.cctv.com',
               }
    req_m3u8 = requests.get(url=url,headers=headers)
    m3u8 = req_m3u8.text
    re_bds1 = '(.*?)[0-9]+\.m3u8'
    pattern1 = re.compile(re_bds1,re.S)
    front = pattern1.findall(url)[0]
    re_bds2 = '([0-9]*?\.ts)'
    pattern2 = re.compile(re_bds2,re.S)
    pre_list = pattern2.findall(m3u8)
    ts_list = [front+pre for pre in pre_list]
    return ts_list

@retry(max_retries=3, sleep_duration=1)
def get_search_cctv_list(**kwarg):
    keyword = kwarg['keyword']
    keyword_quote = parse.quote(keyword)
    cookie = 'cna=92ujHLvFsHMCAW/HRIEHXtnw'
    ua = UA(verify_ssl=False)
    headers = {'User-Agent': ua.random,'Cookie':cookie}
    search_page_url = 'https://v.cctv.com/sousuo/index.shtml?title=' + keyword_quote
    search_page_req = requests.get(url=search_page_url,headers=headers)
    search_page_html = search_page_req.content.decode('utf-8')
    re_bds_search_page = '//media.app.cctv.com/vapi/video/vplist.do\?.*?chid=([A-Za-z0-9]*?)&title='
    pattern_search_page = re.compile(re_bds_search_page,re.S)
    chid = pattern_search_page.findall(search_page_html)[0]
    search_url = 'https://media.app.cctv.com/vapi/video/vplist.do?chid='+chid+'&title='+keyword_quote+'&p=1&n=12'
    search_req = requests.get(url=search_url,headers=headers)
    search_json = search_req.json()
    data_list = search_json['data']
    re_bds_data = 'VIDE(.*?)\.shtml'
    pattern_data = re.compile(re_bds_data,re.S)
    video_id_list = pattern_data.findall(str(data_list))
    return video_id_list


# v.baidu.com

v = WebSiteInfo(get_url=get_url_v,get_file=get_file_v_url)
v.set_ux(config_dict['v'])

WebDict['v'] = v

# haokan.baidu.com

haokan = WebSiteInfo(get_param=get_params_haokan, get_file=get_file_haokan_url,get_search=get_search_haokan_list)
haokan.set_ux(config_dict['haokan'])

WebDict['haokan'] = haokan

# www.ku6.com

ku6 = WebSiteInfo(get_url=get_url_ku6, get_param=get_params_ku6, get_file=get_file_ku6_url)
ku6.set_ux(config_dict['ku6'])

WebDict['ku6'] = ku6

# v.ifeng.com

ifeng = WebSiteInfo(get_url=get_url_ifeng,get_like=get_like_ifeng_url,get_view=get_view_ifeng_url,get_file=get_file_ifeng_url)
ifeng.set_ux(config_dict['ifeng'])

WebDict['ifeng'] = ifeng

# www.thepaper.com

thepaper = WebSiteInfo(get_url=get_url_thepaper,get_like=get_like_thepaper_url,get_file=get_file_thepaper_url,get_search=get_search_thepaper_list)
thepaper.set_ux(config_dict['thepaper'])

WebDict['thepaper'] = thepaper

# www.tudou.com

tudou = WebSiteInfo(get_url=get_url_tudou,get_file=get_file_tudou_url,get_ts=get_ts_tudou_url)
tudou.set_ux(config_dict['tudou'])

WebDict['tudou'] = tudou


# v.cctv.com

cctv = WebSiteInfo(get_url=get_url_cctv,get_like=get_like_cctv_url,get_file=get_file_cctv_url,get_ts=get_ts_cctv_url,get_search=get_search_cctv_list)
cctv.set_ux(config_dict['cctv'])

WebDict['cctv'] = cctv