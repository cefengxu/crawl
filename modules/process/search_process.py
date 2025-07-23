from .base_process import BaseProcess
from ..plugins.base_request_model import SearchModel
from ..plugins.baidu_searcher import BaiduSearcher
from ..plugins.tavily_searcher import TavilySearcher
from ..plugins.exa_searcher import ExaSearcher
from ..plugins.bocha_searcher import BochaSearcher
from ..plugins.arxiv_searcher import ArxivSearcher
from ..plugins.bing_searcher import BingSearcher
import time

class SearchProcess(BaseProcess):
    def __init__(self, item: SearchModel):
        self.item = item

    async def process(self, static_manager: dict[str, list] = {}):
        print(f"⏳开始检索: {self.item.query} ⏳")
        
        # self.__init__
        
        results = []
        start_time = time.time()
        if self.item.search_engine == "tavily":
            tavily_search = TavilySearcher(self.item)
            results = await tavily_search.process()
        elif self.item.search_engine == "exa":
            exa_search = ExaSearcher(self.item)
            results = await exa_search.process()
        elif self.item.search_engine == "baidu":
            baidu_search = BaiduSearcher(self.item)
            results = await baidu_search.process()
        elif self.item.search_engine == "bocha":
            bocha_search = BochaSearcher(self.item)
            results = await bocha_search.process()
        elif self.item.search_engine == "arxiv":
            arxiv_search = ArxivSearcher(self.item)
            results = await arxiv_search.process()
            # await self.exa_search()
        elif self.item.search_engine == "bing":
            bing_search = BingSearcher(self.item)
            results = await bing_search.process()

            
        end_time = time.time()
        print(f"⏳检索总耗时:{(end_time - start_time)} 秒")

        return { 'times': (end_time - start_time), 'results': results }