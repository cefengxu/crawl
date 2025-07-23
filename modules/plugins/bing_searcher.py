# from .base_searcher import BaseSearcher
from .base_request_model import SearchModel
from .base_plugin import BasePlugin
import time, requests, json
from exa_py import Exa
from modules.utils.config import Config


class BingSearcher(BasePlugin):
    def __init__(self, item: SearchModel):
        super().__init__(item)
        start_time = time.time()    
        self.subscription_key = Config.app_config.plugins.search.searchers["bing"].subscription_key
        self.endpoint = Config.app_config.plugins.search.searchers["bing"].endpoint
        self.exclude_domains = ["en.wikipedia.org", "www.wikiwand.com", "simple.wikipedia.org", "www.youtube.com",
                                "www.facebook.com"]
        
        # self.exa = Exa(api_key=self.key)
        end_time = time.time()
        print(f"⏰Bing初始化用时:{(end_time - start_time) } 秒")

    def change_query(self, query):
        for domain in self.exclude_domains:
            query = query + f" -site:{domain}"
        query = query + " -filetype:pdf"
        return query

    def search_with_requests(self, query,count, **kwargs):
        
        """修改后的搜索方法"""
        params = {
            'q': self.change_query(query),
            'mkt': kwargs.get("mkt", "zh-CN"),
            'count': count
        }

        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}
        

        
        try:
            response = requests.get(self.endpoint, headers=headers, params=params)
            response.raise_for_status()
            json_response = response.json()
            
            results = []
            if 'webPages' in json_response and 'value' in json_response['webPages']:
                for item in json_response['webPages']['value']:
                    results.append({
                        'siteName': item['name'],
                        'url': item['url'],
                        'content': "NA",
                        'snippet': item['snippet'],
                    })
            return results

        except Exception as ex:
            print('[Exception]', ex)
            raise ex

    def search_with_lib(self, query,count, **kwargs):
        
        pass
          
    def search(self, query,count, **kwargs):
        start_time = time.time()
        
        results = self.search_with_requests(query,count, mkt = kwargs.get("mkt","zh-CN"))
 
        # results =  self.search_with_lib(query,count, crawler = _crawler)
        # _invoke = kwargs.get("invoke","req")
        end_time = time.time()
        print(f"Bing 基于 req 检索用时:{(end_time - start_time)} 秒")
        return results

    async def process(self):
        return self.search(
            query=self.item.query,
            count=self.item.count,
            # invoke = self.item.params.invoke,
            #crawler = self.item.params.crawler,
            mkt = self.item.params.mkt
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