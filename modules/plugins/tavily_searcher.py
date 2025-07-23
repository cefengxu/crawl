# from .base_searcher import BaseSearcher
from tavily import TavilyClient
import time
import requests
import json
from modules.utils.config import Config
from .base_request_model import SearchModel
from .base_plugin import BasePlugin

class TavilySearcher(BasePlugin):
    def __init__(self, item: SearchModel):
        super().__init__(item)
        # Tavily特定的初始化代码
        start_time = time.time()
        self.client = TavilyClient(Config.app_config.plugins.search.searchers["tavily"].subscription_key)
        end_time = time.time()
        print(f"⏰Tavity初始化用时:{(end_time - start_time) } 秒")

    def _get_search_params(self, query, count, **kwargs):
        """生成统一的搜索参数配置"""
        return {
            "query": query,
            "topic": "general",
            "search_depth": "basic",
            "chunks_per_source": 1,
            "max_results": count,
            "time_range": None,
            "days": 7,
            "include_raw_content": kwargs.get("crawler", False),
            "include_images": False,
            "include_image_descriptions": False,
            "include_domains": [],
            "exclude_domains": ["en.wikipedia.org", "www.wikiwand.com", "simple.wikipedia.org", "www.youtube.com", "www.facebook.com"]
        }

    def search_with_lib(self, query, count, **kwargs):
        try:
            search_params = self._get_search_params(query, count, **kwargs)
            json_response = self.client.search(**search_params)
        except Exception as ex:
            print('[Exception]', ex)
            raise ex

        tavily_results = []
        for item in json_response['results']:
            tavily_results.append({
                'siteName': item['title'],
                'snippet': item['content'],
                'url': item['url'],
                'content': item['raw_content'] if item['raw_content'] else 'NA'
            }) 
        return tavily_results

    def search_with_requests(self, query, count, **kwargs):
        headers = {
            'Authorization': f'Bearer {Config.app_config.plugins.search.searchers["tavily"].subscription_key}',
            'Content-Type': 'application/json'
        }
        
        payload = self._get_search_params(query, count, **kwargs)
        # 为HTTP API特别设置include_answer参数
        payload["include_answer"] = False
        
        try:
            response = requests.post(
                Config.app_config.plugins.search.searchers["tavily"].endpoint,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            
            json_response = response.json()
            tavily_results = []
            
            for item in json_response['results']:
                tavily_results.append({
                    'siteName': item['title'],
                    'snippet': item['content'],
                    'url': item['url'],
                    'content': item.get('raw_content', 'NA')
                })
                
            return tavily_results
            
        except Exception as ex:
            print('[Exception]', ex)
            raise ex

    def search(self, query,count, **kwargs):
        # 实现Tavily特定的搜索逻辑

        start_time = time.time()
        _invoke = kwargs.get("invoke","rest") 
        if _invoke == "rest":
            results = self.search_with_requests(query,count,crawler=kwargs.get("crawler",False))
        else:
            results = self.search_with_lib(query,count,crawler=kwargs.get("crawler",False))
        end_time = time.time()
        print(f"⏰Tavily 基于 {_invoke} 检索用时:{(end_time - start_time)} 秒")

        return results

    
    async def process(self):
        
        return self.search(
            query=self.item.query,
            count=self.item.count,
            crawler = self.item.params.crawler
        )

# tavily_searcher = TavilySearcher()
# res = tavily_searcher.search("what is the meaning of life?",3)
# print(f"\n type:{type(res)}\n lenght:{len(res)}\n{res}")