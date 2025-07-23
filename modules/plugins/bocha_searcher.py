# from .base_searcher import BaseSearcher
from .base_request_model import SearchModel
from .base_plugin import BasePlugin
import time, requests, json
from modules.utils.config import Config


class BochaSearcher(BasePlugin):
    def __init__(self, item: SearchModel):
        super().__init__(item)
        start_time = time.time()    
        self.key = Config.app_config.plugins.search.searchers["bocha"].subscription_key
        self.endpoint = Config.app_config.plugins.search.searchers["bocha"].endpoint
        # self.exclude_domains = 
        
        # self.exa = Exa(api_key=self.key)
        end_time = time.time()
        print(f"⏰Exa初始化用时:{(end_time - start_time) } 秒")

    def search_with_requests(self, query,count, **kwargs):
        """修改后的搜索方法"""
        params = json.dumps({
            "query": query,
            "count": count,
            "page": 1,
            "freshness": "all"
            })
        
        # logger_koba.info("[search todo ]")
        headers = {
            'Authorization': f"Bearer {self.key}",
            'Content-Type': 'application/json'
            }
        
        try:
            start_time = time.time()
            response = requests.post(self.endpoint, headers=headers, data=params)
            # response.raise_for_status()
            end_time = time.time()
            print(f"⏰Bocha 检索用时:{(end_time - start_time)} 秒")
            json_response = response.json()
            print(f"🥺原始结果是：\n{json_response}")
            
            results = []
            if json_response.get('data') and json_response['data'].get('webPages'):
                web_pages = json_response['data']['webPages'].get('value', [])
                for item in web_pages:
                    results.append({
                        'siteName': item.get('name', ''),
                        'url': item.get('url', ''),
                        'content': 'NA',  # 使用snippet作为content
                        'snippet': item.get('snippet', ''),
                    })
            
            print(f"🥺结果是：\n{results}")
            return results

        except Exception as ex:
            print('[Exception]', ex)
            raise ex
        
        

        # response = requests.post(self.endpoint, headers=headers, data=params)
        # result = response.json()
        # return result

    # def search_with_lib(self, query,count, **kwargs):
        
    #     try:
    #         if kwargs.get("crawler",False) :
    #             result = self.exa.search_and_contents(
    #                 query,
    #                 exclude_domains = ["en.wikipedia.org", "www.wikiwand.com", "simple.wikipedia.org", "www.youtube.com", "www.facebook.com"],
    #                 livecrawl = "fallback",
    #                 livecrawl_timeout = 1000,
    #                 text = True,
    #                 num_results = count,
    #                 type = "auto"
    #                 )
    #         else:
    #             result = self.exa.search(
    #                 query,
    #                 exclude_text = ["en.wikipedia.org,www.wikiwand.com, simple.wikipedia.org, www.youtube.com, www.facebook.com"],
    #                 type = "auto",
    #                 num_results = count
    #                 )
    #     except Exception as ex:
    #         print('[Exception]', ex)
    #         raise ex

    #     exa_results = []

    #     for item in result.results:
    #         exa_results.append({
    #                 'siteName': item.title,
    #                 'snippet': 'NA',
    #                 'url': item.url,
    #                 'content': item.text if item.text else '', #content  # 添加网页内容
    #             }) 
    #     # print(f"\n{type(result)}\n{result.resu}")
    #     return exa_results
          
    def search(self, query,count, **kwargs):
        start_time = time.time()
        
        results = self.search_with_requests(query,count)
 
        # results =  self.search_with_lib(query,count, crawler = _crawler)
        # _invoke = kwargs.get("invoke","req")
        end_time = time.time()
        print(f"⏰Bocha检索用时:{(end_time - start_time)} 秒")
        return results

    async def process(self):
        return self.search(
            query=self.item.query,
            count=self.item.count,
            invoke = self.item.params.invoke,
            crawler = self.item.params.crawler
        )

     
# bocha_searcher = BochaSearcher()
# res = bocha_searcher.search("what is the meaning of life?",1)
# print(f"结果是：\n{res}")

# exa = Exa('dbe695c7-5a6c-4992-b1a3-e11a6b1f4c22')
# result_with_text = exa.search_and_contents(
#     "AI in healthcare",
#     text=True,
#     highlights=True,
#     num_results=1
# )
# print(f"结果是：\n{result_with_text}")