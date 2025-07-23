import asyncio
import os
import sys
import time
import uuid
from multiprocessing import Manager
from threading import Lock
from typing import Optional, Dict, Any

from dask.distributed import Client
from dask.distributed import Future

from .process.base_process import BaseProcess
from .utils.koba_logger import KobaLogger
from .utils.config import Config

from .process.static.playwright_static import PlaywrightStatic
from .process.static.selenium_static import SeleniumStatic
# from .process.static.rerank_static import RerankerStatic

class TaskModel:
    progress: int = 0
    start_time: float = time.time()
    cancelled: bool = False
    process: Optional[BaseProcess]
    future: Optional[Future] = None  # 存储Dask Future引用


class TaskProgressManager:
    _instance = None
    _lock = Lock()
    _dask_client = None  # 添加客户端引用
    static_manager: dict[str, list] = {}
    task_manager: 'TaskProgressManager'

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                # 创建新实例
                instance = super(TaskProgressManager, cls).__new__(cls)
                # _initialized 用于确保 __init__ 逻辑只执行一次
                # setattr 用于动态添加属性，避免静态类型检查器关于未定义属性的警告
                setattr(instance, '_initialized', False)
                
                # 设置单例实例引用
                cls._instance = instance
                cls.task_manager = instance  # 保证 task_manager 被设置为创建的实例
            
            # 此时，cls._instance 和 cls.task_manager 都引用有效的单例实例
            return cls._instance

    def __init__(self):
        # 检查 _initialized 属性是否存在且为 False，确保初始化逻辑仅执行一次
        if not getattr(self, '_initialized', True): # Safely check _initialized
            print(" * 初始化任务进度管理器...")
            self._tasks: Dict[str, TaskModel] = {}
            self._task_lock = Lock()
            self._initialized = True
            self._cancelled_tasks = set()  # 新增：用于存储已取消的任务ID

            # 创建进程间共享字典用于任务取消状态
            self._manager = Manager()
            self._shared_cancel_states = self._manager.dict()

    def _ensure_client(self):
        """确保Dask客户端已初始化,并配置合适的资源限制"""
        if self._dask_client is None:
            # 设置合理的进程和线程数，根据服务器性能调整
            cpu_count = os.cpu_count() or Config.app_config.service.cpu_core_num  # 如果无法获取CPU数量，默认为20
            n_workers = min(cpu_count, 30)  # 限制最多使用4个核心
            self._dask_client = Client(
                processes=True,
                n_workers=n_workers,
                threads_per_worker=1,
                memory_limit='32GB'  # 限制内存使用
            )
            
            actor_beta_future = self._dask_client.submit(SeleniumStatic, actor=True)
            actor_beta = actor_beta_future.result()
            self.static_manager['selenium'] = []
            self.static_manager['selenium'].append(actor_beta)

            self.static_manager['playwright'] = []
            playwright_process_num = Config.app_config.plugins.fetcher.playwright.process_num
            for i in range(playwright_process_num):
                actor_playwright_future = self._dask_client.submit(PlaywrightStatic, actor=True)
                actor_playwright = actor_playwright_future.result()
                self.static_manager['playwright'].append(actor_playwright)
            
            
            # actor_reranker_future = self._dask_client.submit(RerankerStatic, actor=True)
            # actor_reranker = actor_reranker_future.result()
            # self.static_manager['reranker'] = []
            # self.static_manager['reranker'].append(actor_reranker)
            
        return self._dask_client

    def register_task(self, task_id: Optional[str], process: BaseProcess) -> None:
        """init"""
        with self._task_lock:
            if task_id not in self._tasks:
                if task_id is None:
                    task_id = str(uuid.uuid4())
                self._tasks[task_id] = TaskModel()
                self._tasks[task_id].progress = 0
                self._tasks[task_id].start_time = time.time()
                self._tasks[task_id].cancelled = False
                self._tasks[task_id].process = process
                print(f" * 注册任务 {task_id} 成功")
                print(f" * 任务列表: \n {self._tasks} ")
                print(f" * 任务数量: {len(self._tasks)} ")

    @staticmethod
    def _execute_process(process_object: BaseProcess, task_id: str, shared_cancel_states, static_manager: dict[str, list], module_path=None):
        """在Dask工作进程中执行处理并返回结果"""
        
        k = KobaLogger()
        c = Config()
        
        # 如果提供了模块路径，确保它在sys.path中
        if module_path and module_path not in sys.path:
            sys.path.insert(0, module_path)

        # 为进程设置共享状态检查函数
        def check_cancelled():
            return shared_cancel_states.get(task_id, False)

        # 动态添加检查方法到进程对象
        process_object.check_cancelled = check_cancelled

        # 执行处理
        try:
            # 检查process方法是否为异步方法
            import inspect
            process_method = process_object.process

            if inspect.iscoroutinefunction(process_method):
                # 如果是异步方法，创建一个新的事件循环来运行它
                import asyncio

                # 在当前线程创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    # 在新的事件循环中运行协程
                    result = loop.run_until_complete(process_method(static_manager))
                    return result
                finally:
                    # 关闭事件循环
                    loop.close()
            else:
                # 如果是同步方法，直接调用
                return process_method(static_manager)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"任务执行错误: {e}\n{error_details}")
            raise

    async def process_task(self, task_id: Optional[str]) -> Any:
        """Execute task asynchronously without multiprocessing"""

        if task_id is None:
            raise ValueError('Task ID cannot be None')

        # 确保客户端已初始化
        dask_client = self._ensure_client()

        with self._task_lock:
            if task_id not in self._tasks:
                raise ValueError(f'Task with ID {task_id} not found')

            task = self._tasks[task_id]
            if task.process is None:
                raise ValueError('Task process is not defined')
            task_process = task.process

        # 获取项目根目录路径
        # module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 使用Dask提交任务，传入共享取消状态
        dask_future = dask_client.submit(
            self._execute_process,
            task_process,
            task_id,
            self._shared_cancel_states,
            self.static_manager,
        )

        # 创建一个asyncio的Future
        loop = asyncio.get_event_loop()
        asyncio_future = loop.create_future()

        # 保存Dask Future引用以便后续可能的取消操作
        with self._task_lock:
            self._tasks[task_id].future = dask_future

        # 定义回调函数以处理Dask Future完成时的结果
        def _on_done(f):
            try:
                # 获取结果并在asyncio Future上设置
                result = f.result()
                if not asyncio_future.cancelled():
                    loop.call_soon_threadsafe(asyncio_future.set_result, result)
            except Exception as e:
                # 处理异常情况
                if not asyncio_future.cancelled():
                    loop.call_soon_threadsafe(asyncio_future.set_exception, e)

        # 添加回调
        dask_future.add_done_callback(_on_done)

        # 等待asyncio Future完成，添加超时控制
        try:
            # 设置30分钟超时
            result = await asyncio.wait_for(asyncio_future, timeout=1800)
            return result
        except asyncio.TimeoutError:
            # 处理超时情况
            dask_future.cancel()
            with self._task_lock:
                self._tasks[task_id].cancelled = True
                self._cancelled_tasks.add(task_id)
                # 更新共享状态
                self._shared_cancel_states[task_id] = True
            raise TimeoutError(f"任务 {task_id} 执行超时")
        except asyncio.CancelledError:
            # 处理取消情况
            dask_future.cancel()
            raise

    def cancel_task(self, task_id: str) -> bool:
        """取消指定任务"""
        with self._task_lock:
            if task_id in self._tasks:
                self._tasks[task_id].cancelled = True
                self._cancelled_tasks.add(task_id)

                # 更新共享状态
                self._shared_cancel_states[task_id] = True

                # 如果存在Future引用，尝试取消任务
                future = self._tasks[task_id].future
                if future is not None:
                    future.cancel()

                return True
            return False

    def is_task_cancelled(self, task_id: str) -> bool:
        """检查任务是否已被取消"""
        with self._task_lock:
            if task_id in self._tasks:
                return self._tasks[task_id].cancelled
            return False

    def update_progress(self, task_id: Optional[str], progress: int) -> None:
        """Update progress"""

        if not 0 <= progress <= 100:
            raise ValueError("Progress must be 0-100")

        with self._task_lock:
            if task_id in self._tasks:
                self._tasks[task_id].progress = progress

    def increment_progress(self, task_id: Optional[str], increment: int = 10) -> Optional[int]:
        """Increment progress"""

        with self._task_lock:
            if task_id not in self._tasks:
                return None

            current_progress = self._tasks[task_id].progress
            new_progress = min(100, current_progress + increment)  # 确保不超过100
            self._tasks[task_id].progress = new_progress

            return new_progress

    def get_progress(self, task_id: Optional[str]) -> Optional[int]:
        """get_progress"""

        with self._task_lock:
            print('[-01-]', task_id)
            print('[-02-]', self._tasks)
            if task_id in self._tasks:
                return self._tasks[task_id].progress
            return None

    def remove_task(self, task_id: Optional[str]) -> None:
        """remove_task"""
        with self._task_lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                if task_id in self._cancelled_tasks:
                    self._cancelled_tasks.remove(task_id)

    def get_all_tasks(self) -> Dict[str, TaskModel]:
        """get_all_tasks"""
        with self._task_lock:
            print(f" * 获取任务: \n {self._tasks}")
            return self._tasks.copy()

    def task_exists(self, task_id: str) -> bool:
        """task_exists"""
        with self._task_lock:
            return task_id in self._tasks


# 全局单例实例
# task_manager = TaskProgressManager()

def get_task_manager() -> TaskProgressManager:
    """
    返回 TaskProgressManager 单例实例。主进程入口处先调用一次以完成初始化。
    """
    return TaskProgressManager()
