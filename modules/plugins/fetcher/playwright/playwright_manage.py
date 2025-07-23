import asyncio
from collections import deque
import time
from typing import Optional

#from camoufox import AsyncNewBrowser, Camoufox
from modules.plugins.fetcher.common.fetch_context import FetchContext
from modules.plugins.fetcher.playwright.playwright_pool import AsyncPlayWrightPool, PlayWrightContextWrapper
from modules.plugins.fetcher.playwright.playwright_pool import AsyncPlayWrightPool, PlayWrightWrapper
from modules.utils.singleton import Singleton
from modules.utils.koba_logger import KobaLogger
from playwright.sync_api import TimeoutError
from playwright.async_api import async_playwright
from patchright.async_api import async_playwright as patchright_async_playwright

class PlayWrightManager(metaclass=Singleton):
    def __init__(self,browser_num=1,page_num=1,use_camoufox=False,executable_path=None):
        self.browser_num = browser_num
        self.page_num = page_num
        self.use_camoufox= use_camoufox
        self.executable_path = executable_path
        #self.camoufox_pool:Optional[AsyncPlayWrightPool] = None
        self.chrome_pool:Optional[AsyncPlayWrightPool] = None
        self.task_queue = asyncio.Queue()
        self.wrapper_tasks = deque()
        self.close_event = asyncio.Event()
    
    async def __aenter__(self):
        # 支持异步上下文管理器
        return self

    async def __aexit__(self, *exc_info):
        # 自动清理资源
        pass   

    _instance = None
    _lock = asyncio.Lock()
    @classmethod
    async def create(cls):
        """异步工厂方法，完成完整初始化"""
        if not cls._instance:
            async with cls._lock:  # 使用锁确保线程安全
                if not cls._instance:  # 再次检查，防止多个协程同时创建实例
                    cls._instance = cls()
                    await cls._instance.init_async()
        return cls._instance
    
    async def init_async(self):

        init_complete = asyncio.Event()
        async def init_and_loop():
            #async with async_playwright() as p:
            async with patchright_async_playwright() as p:
                self.chrome_pool = AsyncPlayWrightPool(self.browser_num,self.page_num,executable_path=self.executable_path)
                await self.chrome_pool.init_pool(p,"chrome")
                init_complete.set()
                KobaLogger.logger_koba.info(f"[playwright] init chrome success,max browser:{self.browser_num},max page:{self.page_num}")
                asyncio.create_task(self.combine_task_and_wrapper_loop())
                asyncio.create_task(self.get_batch_and_fetch_loop())
                await self.close_event.wait()
        asyncio.create_task(init_and_loop())
        await init_complete.wait()


    # async def get_batch_and_fetch2(self):
    #     tasks=[]
    #     start=time.time()
    #     self.batch_fetch_complete_event.clear()
    #     while not self.task_queue.empty():
    #         fetch_context,wait_util,browser_type,future= await self.task_queue.get()
    #         browser_wrapper,context_wrapper = await self.get_wrapper_by_bowser_type(browser_type)
    #         tasks.append(self.fetch(browser_wrapper,context_wrapper,fetch_context,future,wait_util,browser_type))
    #         if len(tasks)>=self.page_num:
    #             break
    #     self.batch_fetch_complete_event.set()
    #     if len(tasks)>0:
    #         KobaLogger.logger_koba.info(f"[playwright] get {len(tasks)} task and start fetch,cost:{time.time()-start}s")
    #         await asyncio.gather(*tasks)

    async def combine_task_and_wrapper_loop(self):
        while True:
            try:
                fetch_context,wait_util,browser_type,future= await self.task_queue.get()
                browser_wrapper,context_wrapper = await self.get_wrapper_by_bowser_type(browser_type)
                self.wrapper_tasks.append(self.fetch(browser_wrapper,context_wrapper,fetch_context,future,wait_util,browser_type))
            except Exception as e:
                KobaLogger.logger_koba.error(f"[playwright] combine task and wrapper fail:{e}")
                if fetch_context:
                    await self.task_queue.put((fetch_context,wait_util,browser_type,future))
                if browser_wrapper:
                    await browser_wrapper.release_context(context_wrapper)
    async def get_batch_and_fetch_loop(self):
        while True:
            try:
                batch_size = min(self.page_num, len(self.wrapper_tasks))
                batch = [self.wrapper_tasks.popleft() for _ in range(batch_size)]
                if len(batch) > 0:
                    KobaLogger.logger_koba.info(f"[playwright] get {len(batch)} task and fetch: ")
                    asyncio.create_task(self.batch_fetch(batch))
            except Exception as e:
                KobaLogger.logger_koba.error(f"[playwright] get batch and fetch fail:{e}")
            finally:
                await asyncio.sleep(0.5)

    async def batch_fetch(self,batch):
        try:
            await asyncio.gather(*batch)
        except Exception as e:
            print(f"[playwright] batch fetch fail: {e}")                
        



    async def fetch_queue_and_wait(self,context:FetchContext,wait_util,browser_type):
        future = asyncio.Future()
        await self.task_queue.put((context,wait_util,browser_type,future))
        context = await future
        return context

    async def get_wrapper_by_bowser_type(self,browser_type):
        if browser_type == "chrome":
            if not self.chrome_pool:
                raise Exception("chrome_pool is None")
            browser_wrapper,context = await self.chrome_pool.get_browser_wrapper_and_context()
        # elif browser_type == "camoufox":
        #     if not self.camoufox_pool:
        #         raise Exception("camoufox_pool is None")
        #     browser_wrapper,context = await self.camoufox_pool.get_browser_wrapper_and_context()
        else:
            raise Exception("browser_type error")
        return browser_wrapper,context
        

    async def check_health_and_fetch(self,browser_wrapper:PlayWrightWrapper,context_wrapper:PlayWrightContextWrapper,fetch_context:FetchContext,future,wait_until="commit",browser_type="chrome"):
        try:
            await context_wrapper.check_health()
        except:
            browser_type = browser_wrapper.browser_type
            browser_num = browser_wrapper.browser_num
            browser_context_num = context_wrapper.context_num
            KobaLogger.logger_koba.error("[playwright] {browser_type} {browser_num} context {browser_context_num} check_health error: {e}")
        finally:
            await self.fetch(browser_wrapper,context_wrapper,fetch_context,future,wait_until,browser_type)
    async def fetch(self,browser_wrapper:PlayWrightWrapper,context_wrapper:PlayWrightContextWrapper,fetch_context:FetchContext,future,wait_until="commit",browser_type="chrome"):
        try:
            start = time.time()
            url = fetch_context.url          
            browser_type = browser_wrapper.browser_type
            browser_num = browser_wrapper.browser_num
            browser_context_num = context_wrapper.context_num
            page = context_wrapper.page
            KobaLogger.logger_koba.info(f"[playwright] {browser_type} {browser_num} context {browser_context_num} fetch {url}")
            await page.goto(url,wait_until="commit",timeout=3000)
            #await page.goto(url,wait_until="domcontentloaded",timeout=10000)
            goto_page_complete = time.time()
            await page.wait_for_load_state("domcontentloaded",timeout=5000)
            if wait_until == "commit":
                fetch_context.response.browser_html = await self.wait_async(page,3)
            elif wait_until == "wait_height":
                fetch_context.response.browser_html = await self.wait_height_async(page,3)
            elif wait_until == "wait_text":
                fetch_context.response.browser_html = await self.wait_text_async(page,3)
            else:
                #await page.wait_for_load_state(wait_until,timeout=10000)
                fetch_context.response.browser_html = await self.get_content_with_retry(page)
            end = time.time()
            KobaLogger.logger_koba.info(f"[playwright] {browser_type} {browser_num} context {browser_context_num} fetch {url} complete,goto_page:{goto_page_complete-start:.2f}s,wait:{end-goto_page_complete:.2f}s")
        except TimeoutError as e:
            # 处理超时异常
            KobaLogger.logger_koba.error(f"[playwright] {browser_type} {browser_num} context {browser_context_num} 页面加载超时: {e}")
            fetch_context.status.status = f"{browser_type} fetch timeout"
            fetch_context.status.msg = str(e)
        except  Exception as e:
            KobaLogger.logger_koba.error(f"[playwright] {browser_type} {browser_num} context {browser_context_num}: {e}")
            fetch_context.status.status = f"{browser_type} {browser_type} {browser_num} context {browser_context_num} fetch error"
            fetch_context.status.msg = str(e)
        finally:
            future.set_result(fetch_context)
            if browser_wrapper:
                await browser_wrapper.release_context(context_wrapper)


    async def wait_async(self,page,delay=3):
        start_wait = time.time()
        #html = await page.content()
        html = await self.get_content_with_retry(page)
        len_list=[len(html)]
        time_list = [time.time()-start_wait]
        while True:
            await page.wait_for_timeout(300)
            #new_html = await page.content()
            new_html = await self.get_content_with_retry(page)
            html_len = len(html)
            new_html_len = len(new_html)
            if(new_html_len<html_len):
                new_html_len = html_len
            diff = new_html_len - html_len
            threshold = 128 if html_len*0.1 < 128 else html_len*0.1
            len_list.append(new_html_len)
            html = new_html
            cost = time.time() - start_wait
            add = cost-time_list[-1]
            time_list.append(cost)
            if (new_html_len>1024 and diff<threshold) or cost>delay or cost+add>delay:
                break
            # if cost>delay:
            #     break                           
        len_list_str = "->".join(map(str, len_list))
        time_list_formatted = [round(cost, 2) for cost in time_list]
        time_list_str = "->".join(map(str, time_list_formatted))
        KobaLogger.logger_koba.info(f"wait until: {len_list_str} {time_list_str}")
        return html
    
    async def wait_height_async(self,page,delay=3):
        start_wait = time.time()
        s_content = await self.get_content_with_retry(page)
        height = await page.evaluate("() => document.documentElement.scrollHeight")
        time_list = [time.time()-start_wait]
        height_length = [height]
        while True:
            await page.wait_for_timeout(300)
            last_height = await page.evaluate("() => document.documentElement.scrollHeight")
            height_length.append(last_height)
            cost = time.time() - start_wait
            time_list.append(f"{cost:.2f}")
            if (cost>delay):
                break
        end_content = await self.get_content_with_retry(page)
        height_length_str = "->".join(map(str, height_length))
        time_list_str = "->".join(map(str, time_list))
        KobaLogger.logger_koba.info(f"height wait until: {height_length_str} {time_list_str}")
        KobaLogger.logger_koba.info(f"length change: {len(s_content)}->{len(end_content)}")
        return  end_content
    
    async def wait_text_async(self,page,delay=3):
        start_wait = time.time()
        s_content = await self.get_content_with_retry(page)
        text_content = await page.locator("body").text_content() or ""
        length = len(text_content)
        time_list = [f"{time.time()-start_wait:.2f}"]
        length_list = [length]
        while True:
            await page.wait_for_timeout(300)
            last_text_content = await page.locator("body").text_content() or ""
            last_length = len(text_content)
            length_list.append(last_length)
            cost = time.time() - start_wait
            time_list.append(f"{cost:.2f}")
            if (cost>delay):
                break
        end_content = await self.get_content_with_retry(page)
        height_length_str = "->".join(map(str, length_list))
        time_list_str = "->".join(map(str, time_list))
        KobaLogger.logger_koba.info(f"text wait until: {height_length_str} {time_list_str}")
        KobaLogger.logger_koba.info(f"length change: {len(s_content)}->{len(end_content)}")
        return  end_content
    
    async def get_content_with_retry(self,page):
        try:
            content = await page.content()
            return content
        except Exception as ex:
            KobaLogger.logger_koba.warning(f"get content fail: {ex},retry")
            await page.wait_for_load_state("domcontentloaded",timeout=5000)
            content = await page.content()
            return content
    
    @classmethod
    async def cleanup(cls):
        if cls._instance:
            cls._instance.chrome_pool.clean_async()
            cls._instance = None