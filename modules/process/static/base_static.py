from pydantic import BaseModel
from ...utils.koba_logger import KobaLogger

class BaseStatic:
    def __init__(self):
        k = KobaLogger()
    
    async def process(self, item: BaseModel):
        pass