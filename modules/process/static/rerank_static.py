from .base_static import BaseStatic
import asyncio
from ...plugins.reranker.qwen3.reranker_manager import RerankerManager

class RerankerStatic(BaseStatic):
    def __init__(self):
        super().__init__()
        self.reranker = RerankerManager()
        
    async def rerank(self, text_1, text_2, instruction):
        return await self.reranker.rerank(text_1, text_2, instruction)
        