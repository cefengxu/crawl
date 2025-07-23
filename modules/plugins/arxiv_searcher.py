
from .base_plugin import BasePlugin
import arxiv

import time
from .base_request_model import SearchModel

class ArxivSearcher(BasePlugin):
    def __init__(self, item: SearchModel):
        super().__init__(item)
        
        start_time = time.time()
        
        end_time = time.time()
        print(f"⏰Arxiv初始化用时:{(end_time - start_time) } 秒")

    def search(self, query,count, **kwargs):
        # 实现Tavily特定的搜索逻辑

        start_time = time.time()
        
        client = arxiv.Client()
        
        search = arxiv.Search(
            query = query,
            max_results = count,
            sort_by = arxiv.SortCriterion.SubmittedDate
        )
        
        arxiv_results = []
        
        for r in client.results(search):
            arxiv_results.append({
                'summary': r.summary,
                'title': r.title,
                'updated': r.updated,
                'published': r.published,
                'authors': r.authors,
                'url': r.pdf_url,
                'comment': r.comment
            })
            
        end_time = time.time()
        print(f"⏰Arxiv检索用时:{(end_time - start_time)} 秒")

        return arxiv_results

    async def process(self):
        return self.search(
            query=self.item.query,
            count=self.item.count
        )

# tavily_searcher = BaiduSearcher()
# res = tavily_searcher.search("what is the meaning of life?",3)
# print(f"\n type:{type(res)}\n lenght:{len(res)}\n{res}")