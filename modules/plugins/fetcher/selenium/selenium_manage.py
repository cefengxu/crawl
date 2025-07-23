import asyncio

from modules.plugins.fetcher.common.fetch_context import FetchContext
from ..common.s_logging import fetch_logger
import threading
import concurrent.futures
from .selenium_driver_pool import SeleniumDriverPool

import queue

class SeleniumManage():
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SeleniumManage, cls).__new__(cls)
        return cls._instance

    def __init__(self, driver_num: int=1, url: str = None, type: str = "driver", uc=False, page_load_strategy="none",executable_path="/opt/ungooled-chromium/chrome"):
        if not hasattr(self, 'initialized'):
            try:
                self.driver_pool = SeleniumDriverPool(url, driver_num, type=type, uc=uc, page_load_strategy=page_load_strategy,executable_path=executable_path)
                self.task_queue = queue.Queue()
                threading.Thread(target=self.scheduler_loop, daemon=True).start()
                self.initialized = True
            except Exception as e:
                fetch_logger.error(f"drivers init fail:{e}")
                raise e
        

    def scheduler_loop(self):
        """调度器循环：从队列取任务并分配 WebDriver"""
        while True:
            try:
                method_name, args, kwargs, future = self.task_queue.get()
                self.task_queue.task_done()
                driver = self.driver_pool.acquire()
                # 传递所有必要参数到处理线程
                threading.Thread(
                    target=self.process_task_wait_timeout,
                    args=(driver, method_name, args, kwargs, future)  # 新增三个参数
                ).start()
            except Exception as e:
                fetch_logger.error(e)

    def process_task_wait_timeout(self, driver, method_name, args, kwargs, future):
        try:
            process_future = concurrent.futures.Future()
            threading.Thread(
                target=self.process_task,
                args=(driver, method_name, args, kwargs, process_future)  # 新增三个参数
            ).start()
            res = process_future.result(timeout=10)
            future.set_result(res)
        except concurrent.futures.TimeoutError as e:
            fetch_logger.error(f"selenium process task timeout:{e}")
            future.set_exception(e)
        except Exception as e:
            future.set_exception(e)
        finally:
            self.driver_pool.release(driver)
    def process_task(self, driver, method_name, args, kwargs, future):
        """动态调用指定方法"""
        try:
            method = getattr(driver, method_name)  # 反射获取方法
            result = method(*args, **kwargs)       # 带参数执行
            future.set_result(result)
        except AttributeError:
            future.set_exception(AttributeError(f"Method {method_name} not found"))
        except Exception as e:
            future.set_exception(e)
        # finally:
        #     self.driver_pool.release(driver)

    def execute_command(self, method_name: str, *args, **kwargs):
        """通用命令执行方法"""
        future = concurrent.futures.Future()
        self.task_queue.put((method_name, args, kwargs, future))
        res = future.result(timeout=30)
        return res

    def get_html(self, url):
        try:
            fetch_logger.info(f"{url} Executing command: get_html")
            html = self.execute_command('get_html', url)
            fetch_logger.info(f"{url} Executing command end")
            return html,None
        except concurrent.futures.TimeoutError:
            fetch_logger.error(f"{url} Executing command: get_html timeout")
            return None,"selenium timeout"
        except Exception as e:
            fetch_logger.error(f"{url} Executing command: get_html fail:{e}")
            return None,"selenium error"
    
    async def get_html_async(self, url,queue):
        res = self.execute_command('get_html', url)       
        await queue.put(res)
    
    @classmethod
    def clear_all_driver(cls):
        if cls._instance:
            cls._instance.driver_pool.close_all()
            cls._instance = None
