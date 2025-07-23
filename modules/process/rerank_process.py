from .base_process import BaseProcess
from ..plugins.base_request_model import RerankRequest

import time

class RerankerProcess(BaseProcess):
    def __init__(self, item: RerankRequest):
        self.item = item
        # self.reranker = RerankerManager()

    async def process(self, static_manager: dict[str, list] = {}):
        print(f"⏳开始重排: {self.item}⏳")
        start_time = time.time()
        
        reranker_result = static_manager.get("reranker")[0].rerank( self.item.text_1, self.item.text_2, self.item.instruction).result()
        
        print(f"⏳重排结果: {reranker_result}⏳")
        # prompts = process_inputs(self.item.text_1, self.item.text_2, self.item.instruction)
        
        end_time = time.time()
        print(f"⏳重排总耗时:{(end_time - start_time)} 秒")
        return { 'times': (end_time - start_time), 'results': reranker_result }
        
