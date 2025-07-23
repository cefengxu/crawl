from locale import THOUSEP
from matplotlib.backend_bases import key_press_handler

from modules.plugins.fetcher.common.fetch_context import FetchContext
from .base_process import BaseProcess
from ..plugins.base_request_model import SearchModelBusiness
from ..plugins.base_request_model import FetchModelBusiness
from .search_process_business import SearchProcessBusiness
from .fetch_process_business import FetchProcessBusiness
from .rerank_process import RerankerProcess
from ..plugins.base_request_model import RerankRequest
from ..plugins.reranker_compressor import RerankerCompressor
import time
# import numpy as np

class CrawlProcess(BaseProcess):
    def __init__(self, item: SearchModelBusiness):
        self.item = item
        self.key = item.key


    async def process(self, static_manager: dict[str, list] = {}):
        
        search_process = SearchProcessBusiness(self.item)
        search_result = await search_process.process(static_manager)
        start_time = time.time()
        # print(f"[+]:{search_result}")
        for i  in  range(len(search_result['results'])):
            print(f"[+]:{search_result['results'][i]}")   
            fetch_item = FetchModelBusiness(
                url=search_result['results'][i]['url'],
                fetch_engine=self.item.fetch_engine,
                parser="sum_v2",
                task_id=self.item.task_id,
                key=self.key
            )
            fetch_process = FetchProcessBusiness(fetch_item)
            fetch_result = await fetch_process.process(static_manager)
            
            search_result['results'][i]['content'] = fetch_result['results'].response.final_md
            end_time = time.time()
            print(f"⏳爬取总耗时:{(end_time - start_time)} 秒")
            
            return { 'times': (end_time - start_time), 'results': search_result }
            
            # search_result['results'][i]['content'] = fetch_result['results'].response.final_md
            
            #---------------------------------#
            _reranker_compressor = RerankerCompressor({
                "refiner": {
                    "reranker_initial_threshold": 0.5,
                    "reranker_step_threshold": 0.5,
                    "reranker_split_level_list": [256]
                }
            })
            content_list = _reranker_compressor.get_split_text(fetch_result['results'].response.final_md,  1024)
            content_list_id = [str(i) for i in range(len(content_list))]
            
            pair_list=[]
            for q, ds in zip([self.item.query], [content_list]):
                # 构建请求体
                for d in ds:
                    pair_list.append({"query": q, "doc": d})
                    # get all q for text_1
                    text_1_list = [pair["query"] for pair in pair_list]
                    # get all d for text_2
                    text_2_list = [pair["doc"] for pair in pair_list]
            
            # reranker_result = await self.reranker.async_rerank([user_query], [content_list], [content_list_id], 3, initial_threshold)
            
            
            reranker_item = RerankRequest(
                text_1 = text_1_list,
                text_2 = text_2_list,
                instruction="根据用户查询，检索相关的段落"
            )
            _reranker_process = RerankerProcess(reranker_item)
            reranker_result = await _reranker_process.process(static_manager)
            
            # reranker_process = RerankerProcess(text_1_list, text_2_list, "根据用户查询，检索相关的段落")
            # reranker_result = reranker_process.process()
            response_data = reranker_result['results']['results']
            score_list = [item['score'] for item in response_data]
            # Reshape score_list to match the shape of chunk_list
            # lens = [len(ds) for ds in content_list]
            # score_list = np.array(score_list)
            # score_list = np.split(score_list, np.cumsum(lens)[:-1])
            # score_list = [list(map(float, sl)) for sl in score_list]
            # log_item = [[round(score, 3) for score in score_list_] for score_list_ in score_list]

            # threshold = threshold_after_norm if threshold_after_norm is not None else self.rerank_thresh
            threshold = 0.05
            topk = 3
            result = []
            for (score, content, id) in zip(score_list, content_list, content_list_id):
                if score <= threshold:
                    continue
                result.append(
                        {
                        "score": score,
                        "content": content,
                        "chunkId": id,
                        }
                )
            # Sort each sublist in result by score descending, then take top-n for each
            final_result = sorted(result, key=lambda x: x['score'], reverse=True)[:topk]

            
            reranker_result = final_result
           
            #sort by id
            sorted_id_result = sorted(reranker_result, key=lambda x: x['chunkId'])
            chunk_result = ''.join([node["content"] for node in sorted_id_result])
            if len(reranker_result) > 0:
                # 获取最大值
                max_value = reranker_result[0]["score"]
            else:
                # 如果没有结果，设置最大值为0
                max_value = 0
            
            search_result['results'][i]['content'] = chunk_result
            #---------------------------------#
            
            
            # fetch_process = FetchProcessBusiness(val)
            # fetch_result = await fetch_process.process()
            # search_process['reslut'][i]['fetch_result'] = fetch_result
        
        # print(f"[+]:{search_result}")
        end_time = time.time()
        print(f"⏳爬取总耗时:{(end_time - start_time)} 秒")
        return { 'times': (end_time - start_time), 'results': search_result }
        
        # fetch_process = FetchProcessBusiness(self.fetch_item)
        
        # search_result = await search_process.process()
        # fetch_result = await fetch_process.process()
        
        # return search_result, fetch_result
    