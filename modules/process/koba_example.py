from .base_process import BaseProcess
from pydantic import BaseModel, Field
from typing import Optional,Any
import uuid
import time
import asyncio

class ExampleModel(BaseModel):
    query: str
    task_id: Optional[str] = None

    def __init__(self, **data):
        if 'task_id' not in data or data['task_id'] is None:
            data['task_id'] = str(uuid.uuid4())
        super().__init__(**data)

class ExampleProcess(BaseProcess):
    def __init__(self, item: ExampleModel):
        # self.item = item
        # self.searcher = BingSearch(item)
        self.query = item.query

    async def process(self, static_manager: dict[str, list] = {}):
        start_time = time.time()
        # responses = await self.searcher.process()
        await asyncio.sleep(10)
        end_time = time.time()

        result = {
            'times': (end_time - start_time) * 1000,
            'result': self.query,
            # 'version': self.VERSION
        }
        return result
