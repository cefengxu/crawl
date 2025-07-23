from .base_process import BaseProcess
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
import uuid
import time
from ..plugins.open_weather import OpenWeather
from ..plugins.base_request_model import WeatherModel

# class WeatherModel(BaseProcess):
#     # location: str
#     # format: Optional[str] = Field(default="metric")  # metric / imperial / standard
#     # num_days: Optional[int] = Field(default=3)
#     # task_id: Optional[str] = None

#     def __init__(self, item: WeatherModel):
#         if 'task_id' not in data or data['task_id'] is None:
#             data['task_id'] = str(uuid.uuid4())
#         super().__init__(**data)

class WeatherProcess(BaseProcess):
    def __init__(self, item: WeatherModel):
        self.item = item

    async def process(self, static_manager: dict[str, list] = {}):
        print(f"⏳开始查询天气: {self.item.location} ⏳")
        
        results = []
        start_time = time.time()
        open_weather = OpenWeather(self.item)
        results = await open_weather.process()
        end_time = time.time()
        print(f"⏳查询天气总耗时:{(end_time - start_time)} 秒")
        return { 'times': (end_time - start_time), 'results': results }