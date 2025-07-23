#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by xufeng8, 2025


import sys
import requests
from bs4 import BeautifulSoup
import random
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


ABSTRACT_MAX_LENGTH = 300    # abstract max length

# 扩展User-Agent池
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

# 扩展请求头
def get_random_headers():
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "User-Agent": random.choice(user_agents),
        "Referer": "https://www.baidu.com/",
        "Upgrade-Insecure-Requests": "1",
        "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
        "sec-ch-ua-mobile": "?0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }

baidu_host_url = "https://www.baidu.com"
baidu_search_url = "https://www.baidu.com/s?ie=utf-8&tn=baidu&wd="

# 配置重试策略
retry_strategy = Retry(
    total=3,  # 最大重试次数
    backoff_factor=1,  # 重试间隔
    status_forcelist=[500, 502, 503, 504, 429]  # 需要重试的HTTP状态码
)

# 创建会话
session = requests.Session()
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

def add_random_delay(min_delay=0.3, max_delay=0.5):
    """添加随机延时"""
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

def search(keyword, num_results=10, debug=0):
    """搜索函数"""
    if not keyword:
        return None

    list_result = []
    page = 1
    consecutive_empty_results = 0  # 连续空结果计数
    max_empty_results = 3  # 最大允许的连续空结果次数

    next_url = baidu_search_url + keyword

    while len(list_result) < num_results:
        # 更新请求头
        session.headers = get_random_headers()
        
        # 添加随机延时
        add_random_delay()

        data, next_url = parse_html(next_url, rank_start=len(list_result), debug=debug)
        
        if data:
            list_result += data
            consecutive_empty_results = 0  # 重置计数器
            if debug:
                print("---searching[{}], finish parsing page {}, results number={}: ".format(keyword, page, len(data)))
        else:
            consecutive_empty_results += 1
            if consecutive_empty_results >= max_empty_results:
                if debug:
                    print("连续{}次未获取到结果，停止搜索".format(max_empty_results))
                break

        if not next_url:
            if debug:
                print("已到达最后一页")
            break
            
        page += 1

    if debug:
        print("\n---search [{}] finished. total results number={}！".format(keyword, len(list_result)))
    return list_result[: num_results] if len(list_result) > num_results else list_result


from requests.exceptions import RequestException

def parse_html(url, rank_start=0, debug=0):
    """解析HTML页面"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 添加随机延时
            add_random_delay(0.3, 0.5)
            
            res = session.get(url=url, timeout=10)
            res.raise_for_status()
            res.encoding = "utf-8"
            
            if "verify" in res.url.lower() or "login" in res.url.lower():
                if debug:
                    print("检测到验证码或登录页面")
                return None, None
                
            root = BeautifulSoup(res.text, "lxml")
            
            # 检查是否被封禁
            if "您的访问出现异常" in res.text or "您的网络存在异常访问" in res.text:
                if debug:
                    print("检测到访问被限制")
                return None, None

            # 添加调试信息
            if debug:
                print(f"页面内容长度: {len(res.text)}")
                print("开始查找content_left div...")

            list_data = []
            div_contents = root.find("div", id="content_left")
            
            # 检查div_contents是否为None
            if div_contents is None:
                if debug:
                    print("未找到content_left div，尝试查找其他可能的结果容器...")
                    print("页面标题:", root.title.text if root.title else "无标题")
                return None, None

            if debug:
                print(f"找到content_left div，包含 {len(div_contents.contents)} 个子元素")

            for div in div_contents.contents:
                if type(div) != type(div_contents):
                    continue

                class_list = div.get("class", [])
                if not class_list:
                    continue

                if "c-container" not in class_list:
                    continue

                title = ''
                url = ''
                abstract = ''
                try:
                    # 遍历所有找到的结果，取得标题和概要内容（50字以内）
                    if "xpath-log" in class_list:
                        if div.h3:
                            title = div.h3.text.strip()
                            url = div.h3.a['href'].strip()
                        else:
                            title = div.text.strip().split("\n", 1)[0]
                            if div.a:
                                url = div.a['href'].strip()

                        if div.find("div", class_="c-abstract"):
                            abstract = div.find("div", class_="c-abstract").text.strip()
                        elif div.div:
                            abstract = div.div.text.strip()
                        else:
                            abstract = div.text.strip().split("\n", 1)[1].strip()
                    elif "result-op" in class_list:
                        if div.h3:
                            title = div.h3.text.strip()
                            url = div.h3.a['href'].strip()
                        else:
                            title = div.text.strip().split("\n", 1)[0]
                            url = div.a['href'].strip()
                        if div.find("div", class_="c-abstract"):
                            abstract = div.find("div", class_="c-abstract").text.strip()
                        elif div.div:
                            abstract = div.div.text.strip()
                        else:
                            # abstract = div.text.strip()
                            abstract = div.text.strip().split("\n", 1)[1].strip()
                    else:
                        if div.get("tpl", "") != "se_com_default":
                            if div.get("tpl", "") == "se_st_com_abstract":
                                if len(div.contents) >= 1:
                                    title = div.h3.text.strip()
                                    if div.find("div", class_="c-abstract"):
                                        abstract = div.find("div", class_="c-abstract").text.strip()
                                    elif div.div:
                                        abstract = div.div.text.strip()
                                    else:
                                        abstract = div.text.strip()
                            else:
                                if len(div.contents) >= 2:
                                    if div.h3:
                                        title = div.h3.text.strip()
                                        url = div.h3.a['href'].strip()
                                    else:
                                        title = div.contents[0].text.strip()
                                        url = div.h3.a['href'].strip()
                                    # abstract = div.contents[-1].text
                                    if div.find("div", class_="c-abstract"):
                                        abstract = div.find("div", class_="c-abstract").text.strip()
                                    elif div.div:
                                        abstract = div.div.text.strip()
                                    else:
                                        abstract = div.text.strip()
                        else:
                            if div.h3:
                                title = div.h3.text.strip()
                                url = div.h3.a['href'].strip()
                            else:
                                title = div.contents[0].text.strip()
                                url = div.h3.a['href'].strip()
                            if div.find("div", class_="c-abstract"):
                                abstract = div.find("div", class_="c-abstract").text.strip()
                            elif div.div:
                                abstract = div.div.text.strip()
                            else:
                                abstract = div.text.strip()
                except Exception as e:
                    if debug:
                        print("catch exception duration parsing page html, e={}".format(e))
                    continue

                if ABSTRACT_MAX_LENGTH and len(abstract) > ABSTRACT_MAX_LENGTH:
                    abstract = abstract[:ABSTRACT_MAX_LENGTH]

                rank_start+=1
                list_data.append({"title": title, "abstract": abstract, "url": url, "rank": rank_start})


            # find next page button
            next_btn = root.find_all("a", class_="n")

            # last page not any more
            if len(next_btn) <= 0 or u"上一页" in next_btn[-1].text:
                return list_data, None

            next_url = baidu_host_url + next_btn[-1]["href"]
            return list_data, next_url
        except requests.exceptions.RequestException as e:
            retry_count += 1
            if debug:
                print(f"请求失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
            if retry_count >= max_retries:
                return None, None
            add_random_delay(0.5, 1)  # 失败后等待更长时间
            continue
            
        except Exception as e:
            if debug:
                import traceback
                traceback.print_exc()
                print(f"解析异常: {type(e).__name__} - {str(e)}")
            return None, None


def run():
    """
    
    :return:
    """
    default_keyword = u"Amazing Coder"
    num_results = 10
    debug = 0

    prompt = """
    baidusearch: not enough arguments
    [0]keyword: keyword what you want to search
    [1]num_results: number of results
    [2]debug: debug switch, 0-close, 1-open, default-0
    eg: baidusearch NBA
        baidusearch NBA 6
        baidusearch NBA 8 1
    """
    if len(sys.argv) > 3:
        keyword = sys.argv[1]
        try:
            num_results = int(sys.argv[2])
            debug = int(sys.argv[3])
        except:
            pass
    elif len(sys.argv) > 1:
        keyword = sys.argv[1]
    else:
        print(prompt)
        keyword = input("please input keyword: ")
        # sys.exit(1)

    if not keyword:
        keyword = default_keyword

    print("---start search: [{}], expected number of results:[{}].".format(keyword, num_results))
    results = search(keyword, num_results=num_results, debug=debug)

    if isinstance(results, list):
        print("search results：(total[{}]items.)".format(len(results)))
        for res in results:
            print("{}. {}\n   {}\n   {}".format(res['rank'], res["title"], res["abstract"], res["url"]))
    else:
        print("start search: [{}] failed.".format(keyword))


if __name__ == '__main__':
    run()


def _extract_title(div):
    if div.h3:
        return div.h3.text.strip()
    return div.text.strip().split("\n", 1)[0]

def _extract_url(div):
    if div.h3 and div.h3.a:
        return div.h3.a['href'].strip()
    if div.a:
        return div.a['href'].strip()
    return ''
