# from .base_searcher import BaseSearcher
# from typing import Coroutine
import aiohttp
from .base_plugin import BasePlugin
# from baidusearch.baidusearch import search
from .baidu_backend.baiduEngine import search
import time
import asyncio
from .base_request_model import SearchModel
from typing import List, Dict, Any

class BaiduSearcher(BasePlugin):
    def __init__(self, item: SearchModel):
        super().__init__(item)
        self.max_retries = 3
        self.retry_delay = 2
        
        start_time = time.time()
        end_time = time.time()
        print(f"⏰Baidu初始化用时:{(end_time - start_time) } 秒")

    async def search_with_retry(self, query: str, count: int, **kwargs) -> List[Dict[str, Any]]:
        """带重试机制的搜索方法"""
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                results = search(query, num_results=count, debug=0)
                results = await self.get_redirect_results(results)
                end_time = time.time()
                
                if not results:
                    print(f"⚠️ 第{attempt + 1}次尝试未获取到结果")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    return []
                
                print(f"⏰Baidu检索用时:{(end_time - start_time)} 秒，检索内容:{len(results)}")
                
                baidu_results = []
                for result in results:
                    baidu_results.append({
                        'siteName': result['title'],
                        'snippet': result['abstract'],
                        'url': result['url'],
                        'content': "NA"
                    })
                return baidu_results
                
            except Exception as e:
                print(f"❌ 搜索异常 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise Exception(f"搜索失败，已重试{self.max_retries}次: {str(e)}")
        
        return []

    async def process(self):
        """处理搜索请求"""
        try:
            return await self.search_with_retry(
                query=self.item.query,
                count=self.item.count
            )
        except Exception as e:
            print(f"处理搜索请求时发生错误: {str(e)}")
            return []
        
    async def get_redirect_results(self, results):
        tasks = [self.get_redirect_result(result) for result in results]
        results = await asyncio.gather(*tasks)
        return results  # 返回原始结果，因为我们只需要原始的搜索结果
    
    async def get_redirect_result(self, result):
        url = result.get('url')
        if url is None:
            return result
        redirect_url = await self.get_redirect_url(url)
        result['url'] = redirect_url
        return result
    async def get_redirect_url(self, url: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, allow_redirects=False) as response:
                    loc_url = response.headers.get("Location", "")
                    if loc_url == "":
                        loc_url = url
                    return loc_url
        except Exception as e:
            print(f"获取重定向URL时出错: {str(e)}")
            return url  # 如果出错，返回原始 URL

# tavily_searcher = BaiduSearcher()
# res = tavily_searcher.search("what is the meaning of life?",3)
# print(f"\n type:{type(res)}\n lenght:{len(res)}\n{res}")