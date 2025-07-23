# from .base_searcher import BaseSearcher
from .base_request_model import SearchModel
from .base_plugin import BasePlugin
import time, requests, json
from exa_py import Exa
from modules.utils.config import Config


class ExaSearcher(BasePlugin):
    def __init__(self, item: SearchModel):
        super().__init__(item)
        start_time = time.time()    
        self.key = Config.app_config.plugins.search.searchers["exa"].subscription_key
        self.endpoint = Config.app_config.plugins.search.searchers["exa"].endpoint
        # self.exclude_domains = 
        
        self.exa = Exa(api_key=self.key)
        end_time = time.time()
        print(f"⏰Exa初始化用时:{(end_time - start_time) } 秒")

    def search_with_requests(self, query,count, **kwargs):
        params = json.dumps({
                "query": query,
                "type": "auto",
                "category": '',
                "numResults": count,
                "excludeDomains":["en.wikipedia.org","www.wikiwand.com","simple.wikipedia.org","www.youtube.com","www.facebook.com"],
                "contents": {
                    "summary": True,
                    "text": kwargs.get("crawler", False),
                }
            })
        
        headers = {
            'x-api-key': self.key,
            'Content-Type': 'application/json'
        }
        
        try:
            
            response = requests.post(self.endpoint, headers=headers, data=params)
            response.raise_for_status()
            
            
            # logger_koba.info(f"[EXA Search Times] {(end_time - start_time) * 1000} ms" )
            json_response = response.json()
            
            # if engine == 'none' or engine == 'exa_sum' or engine == 'exa_text':
            #     # 处理不需要爬取内容的情况
            results = []
            if 'results' in json_response:
                for item in json_response['results']:

                    results.append({
                        'siteName': item['title'],
                        'url': item['url'],
                        'content': item.get('text', ''),
                        'snippet': item.get('summary', ''),
                    })
            return results
            
            # 使用异步方法获取内容
            start_time = time.time()
            if engine == "selenium":
                results = self.web_fetch_with_pool(json_response, engine="selenium", query=query)
            else:
                results = asyncio.run(self.web_fetch_async(json_response, engine=engine, query=query))
            end_time = time.time()
            
            logger_koba.info(f"[Fetch Times] {(end_time - start_time) * 1000} ms" )
            return results

        except Exception as ex:
            print('[Exception]', ex)
            raise ex
        
        

        response = requests.post(self.endpoint, headers=headers, data=params)
        result = response.json()
        return result

    def search_with_lib(self, query,count, **kwargs):
        
        try:
            if kwargs.get("crawler",False) :
                result = self.exa.search_and_contents(
                    query,
                    exclude_domains = ["en.wikipedia.org", "www.wikiwand.com", "simple.wikipedia.org", "www.youtube.com", "www.facebook.com"],
                    livecrawl = "fallback",
                    livecrawl_timeout = 1000,
                    text = True,
                    num_results = count,
                    type = "auto"
                    )
            else:
                result = self.exa.search(
                    query,
                    exclude_text = ["en.wikipedia.org,www.wikiwand.com, simple.wikipedia.org, www.youtube.com, www.facebook.com"],
                    type = "auto",
                    num_results = count
                    )
        except Exception as ex:
            print('[Exception]', ex)
            raise ex

        exa_results = []

        for item in result.results:
            exa_results.append({
                    'siteName': item.title,
                    'snippet': 'NA',
                    'url': item.url,
                    'content': item.text if item.text else '', #content  # 添加网页内容
                }) 
        # print(f"\n{type(result)}\n{result.resu}")
        return exa_results
          
    def search(self, query,count, **kwargs):
        start_time = time.time()
        
        results = self.search_with_requests(query,count,  crawler = kwargs.get("crawler",False))
 
        # results =  self.search_with_lib(query,count, crawler = _crawler)
        _invoke = kwargs.get("invoke","rest")
        end_time = time.time()
        print(f"⏰Exa 基于 {_invoke} 检索用时:{(end_time - start_time)} 秒")
        return results

    async def process(self):
        return self.search(
            query=self.item.query,
            count=self.item.count,
            invoke = self.item.params.invoke,
            crawler = self.item.params.crawler
        )

     
# exa_searcher = ExaSearcher()
# res = exa_searcher.search("what is the meaning of life?",2)
# print(f"结果是：\n{res}")

# exa = Exa('dbe695c7-5a6c-4992-b1a3-e11a6b1f4c22')
# result_with_text = exa.search_and_contents(
#     "AI in healthcare",
#     text=True,
#     highlights=True,
#     num_results=1
# )
# print(f"结果是：\n{result_with_text}")