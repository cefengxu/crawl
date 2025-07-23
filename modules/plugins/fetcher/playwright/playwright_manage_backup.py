import asyncio
import time
from typing import Optional

from camoufox import AsyncNewBrowser, Camoufox
from modules.plugins.fetcher.common.fetch_context import FetchContext
from modules.plugins.fetcher.playwright.playwright_pool import AsyncPlayWrightPool
from modules.plugins.fetcher.playwright.playwright_pool import AsyncPlayWrightPool, PlayWrightWrapper
from modules.utils.singleton import Singleton
from modules.utils.koba_logger import KobaLogger

class PlayWrightManagerBACKUP(metaclass=Singleton):
    def __init__(self,browser_num=1,page_num=1,use_camoufox=False):
        self.browser_num = browser_num
        self.page_num = page_num
        self.use_camoufox= use_camoufox
        self.camoufox_pool:Optional[AsyncPlayWrightPool] = None
        self.chrome_pool:Optional[AsyncPlayWrightPool] = None
    
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
        if self.use_camoufox:
            self.camoufox_pool = AsyncPlayWrightPool(self.browser_num,self.page_num)
            await self.camoufox_pool.init_pool("camoufox")
            KobaLogger.logger_koba.info(f"[playwright] init camoufox success,max browser:{self.browser_num},max page:{self.page_num}")
        
        self.chrome_pool = AsyncPlayWrightPool(self.browser_num,self.page_num)
        await self.chrome_pool.init_pool("chrome")
        KobaLogger.logger_koba.info(f"[playwright] init chrome success,max browser:{self.browser_num},max page:{self.page_num}")

    async def fetch2(self, context:FetchContext,wait_util="commit",browser_type="chrome"):
        try:
            start = time.time()
            url = context.url
            browser_wrapper: PlayWrightWrapper = None
            if browser_type == "chrome":
                if not self.chrome_pool:
                    raise Exception("chrome_pool is None")
                browser_wrapper = await self.chrome_pool.get_browser_wrapper()
            elif browser_type == "camoufox":
                if not self.camoufox_pool:
                    raise Exception("camoufox_pool is None")
                browser_wrapper = await self.camoufox_pool.get_browser_wrapper()
            else:
                raise Exception("browser_type error")
            get_browser_complete = time.time()
            page = await browser_wrapper.get_page()
            create_page_complete = time.time()
            browser_type = browser_wrapper.browser_type
            browser_num = browser_wrapper.browser_num
            KobaLogger.logger_koba.info(f"[playwright] {browser_type} {browser_num} fetch {url}")
            #await page.set_default_navigation_timeout(30000)
            #await page.set_default_timeout(1000)
            await page.goto(url,wait_until=wait_util)
            goto_page_complete = time.time()
            if wait_util == "commit":
                context.response.browser_html = await self.wait_async(page,3)
            else:
                context.response.browser_html = await page.content()
            end = time.time()
            KobaLogger.logger_koba.info(f"[playwright] {browser_type} {browser_num} fetch {url} complete,cost:{end-start:.2f}s,get_browser:{get_browser_complete-start:.2f}s,create_page:{create_page_complete-get_browser_complete:.2f}s,goto_page:{goto_page_complete-create_page_complete:.2f}s,wait:{end-goto_page_complete:.2f}s")
        except asyncio.TimeoutError:
            KobaLogger.logger_koba.error(f"[playwright] {e}")
            context.status.status = f"{browser_type} fetch timeout"
            context.status.msg = str(e)
        except  Exception as e:
            KobaLogger.logger_koba.error(f"[playwright] {e}")
            context.status.status = f"{browser_type} fetch error"
            context.status.msg = str(e)
        finally:
            if browser_wrapper:
                await browser_wrapper.release_page(page)           
            return context
        

    async def fetch(self, context:FetchContext,wait_util="commit",browser_type="chrome"):
        try:
            start = time.time()
            url = context.url
            browser_wrapper: PlayWrightWrapper = None
            if browser_type == "chrome":
                if not self.chrome_pool:
                    raise Exception("chrome_pool is None")
                browser_wrapper,page = await self.chrome_pool.get_browser_wrapper_and_page()
            elif browser_type == "camoufox":
                if not self.camoufox_pool:
                    raise Exception("camoufox_pool is None")
                browser_wrapper,page = await self.camoufox_pool.get_browser_wrapper_and_page()
            else:
                raise Exception("browser_type error")
            get_browser_complete = time.time()
            #page = await browser_wrapper.get_page()
            create_page_complete = time.time()
            browser_type = browser_wrapper.browser_type
            browser_num = browser_wrapper.browser_num
            KobaLogger.logger_koba.info(f"[playwright] {browser_type} {browser_num} fetch {url}")
            #await page.set_default_navigation_timeout(30000)
            #await page.set_default_timeout(1000)
            await page.goto(url,wait_until=wait_util)
            goto_page_complete = time.time()
            if wait_util == "commit":
                context.response.browser_html = await self.wait_async(page,3)
            else:
                context.response.browser_html = await page.content()
            end = time.time()
            KobaLogger.logger_koba.info(f"[playwright] {browser_type} {browser_num} fetch {url} complete,cost:{end-start:.2f}s,get_browser:{get_browser_complete-start:.2f}s,create_page:{create_page_complete-get_browser_complete:.2f}s,goto_page:{goto_page_complete-create_page_complete:.2f}s,wait:{end-goto_page_complete:.2f}s")
        except  Exception as e:
            KobaLogger.logger_koba.error(f"[playwright] {e}")
            context.status.status = f"{self.browser_type} fetch error"
            context.status.msg = str(e)
        finally:
            if browser_wrapper:
                await browser_wrapper.release_page(page)           
            return context


    async def wait_async(self,page,delay=3):
        start_wait = time.time()
        #await page.wait_for_timeout(2000)
        html = await page.content()
        len_list=[len(html)]
        time_list = [time.time()-start_wait]
        while True:
            await page.wait_for_timeout(100)
            new_html = await page.content()
            html_len = len(html)
            new_html_len = len(new_html)
            if(new_html_len<html_len):
                new_html_len = html_len
            diff = new_html_len - html_len
            threshold = 128 if html_len*0.1 < 128 else html_len*0.1
            len_list.append(new_html_len)
            html = new_html
            cost = time.time() - start_wait
            time_list.append(cost)
            if (new_html_len>1024 and diff<threshold) or cost>delay:
                break
            # if cost>delay:
            #     break                           
        len_list_str = "->".join(map(str, len_list))
        time_list_str = "->".join(map(str, time_list))
        KobaLogger.logger_koba.info(f"wait until: {len_list_str} {time_list_str}")
        return html
    
    @classmethod
    async def cleanup(cls):
        if cls._instance:
            cls._instance.camoufox_pool.clean_async()
            cls._instance = None