from abc import abstractmethod
from typing import Any


class BasePlugin:
    def __init__(self, item: Any):
        self.item = item

    @abstractmethod
    async def process(self) -> Any:
        # 处理逻辑
        pass

    def check_cancelled(self):
        """
        这个方法会被task_manager在任务执行时动态覆盖
        用于检查任务是否被取消
        """
        return False
