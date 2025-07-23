import asyncio
import itertools
from typing import Optional, Sequence

# from camoufox import AsyncCamoufox, Camoufox
# from camoufox import AsyncCamoufox,NewBrowser,AsyncNewBrowser
# from camoufox.pkgman import camoufox_path, launch_path 
from playwright.async_api import async_playwright
from modules.utils.koba_logger import KobaLogger
from ..common.s_logging import fetch_logger

class PlayWrightContextWrapper:
    def __init__(self, browser,context_num=-1):
        self.browser = browser
        self.context_num = context_num
    async def init_context(self):
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        self.context = await self.browser.new_context(
            user_agent = user_agent,
            ignore_https_errors=True,
            bypass_csp=True
        )
        self.page = await self.init_page()

    async def re_init(self):
        await self.context.close()
        await self.init_context()
    async def init_page(self):
        page = await self.context.new_page()
        # 拦截非必要请求
        await page.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in ["image", "stylesheet", "font","media"]
            else route.continue_()
        )
        #page.set_default_navigation_timeout(3000)
        page.set_default_timeout(10000)
        return page
    
    async def check_health(self):
        if self.page.is_closed():
            await self.re_init()

class PlayWrightWrapper:
    def __init__(self, playwright,browser_type,browser_num=-1,max_page=1,executable_path="/opt/ungooled-chromium/chrome"):
        self.playwright = playwright
        self.context_wrappers:Optional[asyncio.Queue[PlayWrightContextWrapper]] = asyncio.Queue()
        #self.pages:Optional[asyncio.Queue] = None
        self.browser_type = browser_type
        self.browser_num = browser_num
        self.executable_path = executable_path
        self.max_page = max_page
        self.browser_reconnecting_event = asyncio.Event()
        self.browser_reconnecting_event.set()

    async def init_wrapper(self):
        await self.init_browser()
        await self.init_contexts()
        self.browser.on("disconnected", self.on_browser_disconnect)

    async def init_browser(self):
        # if self.browser_type == "camoufox":                          
        #     path = launch_path()
        #     self.browser = await self.playwright.firefox.launch(headless=True,args=['--disable-gpu'],executable_path=path,)
        if self.browser_type == "chrome":
            self.browser = await self.playwright.chromium.launch(headless=True,executable_path=self.executable_path)
            #self.browser = await self.playwright.chromium.launch(headless=True,executable_path="/opt/chrome-linux/chrome")
        else:
            raise  Exception("browser_type error")

    async def init_contexts(self):
        for i in range(self.max_page):
            context = PlayWrightContextWrapper(self.browser, i)
            await context.init_context()
            self.context_wrappers.put_nowait(context)


    async def get_context(self):
        await self.check_browser_health()
        context = await self.context_wrappers.get()
        KobaLogger.logger_koba.info(f"{self.browser_type} broswer {self.browser_num} get context {context.context_num},now free contexts: {self.context_wrappers.qsize()}")
        return context
    
    async def get_context_no_wait(self):
        await self.check_browser_health()
        context = self.context_wrappers.get_nowait()
        KobaLogger.logger_koba.info(f"{self.browser_type} broswer {self.browser_num} get context {context.context_num},now free contexts: {self.context_wrappers.qsize()}")
        return context
    
    async def release_context(self, context:PlayWrightContextWrapper):
        #await context.re_init()
        await self.check_browser_health()
        if self.context_wrappers.qsize() < self.max_page:
            await context.re_init()
            await self.context_wrappers.put(context)
            KobaLogger.logger_koba.info(f"{self.browser_type} broswer {self.browser_num} release context {context.context_num},now free contexts: {self.context_wrappers.qsize()}")
        else:
            KobaLogger.logger_koba.warning(f"{self.browser_type} broswer {self.browser_num} release context {context.context_num} fail,contexts are full")

    async def check_browser_health(self):
        await self.browser_reconnecting_event.wait()

    async def on_browser_disconnect(self, browser):
        KobaLogger.logger_koba.info(f"[playwright] browser {self.browser_num} reconnecting......")
        self.browser_reconnecting_event.clear()
        num = 0
        while not self.browser.is_connected():
            try:
                await self.init_wrapper() 
                KobaLogger.logger_koba.info(f"[playwright] browser {self.browser_num} reconnecting success")
                self.browser_reconnecting_event.set()
            except Exception as e:
                if num%100 == 0:
                    KobaLogger.logger_koba.error(f"[playwright] browser {self.browser_num} reconnecting fail:{e},retry:{num}")
                await asyncio.sleep(3)




class AsyncPlayWrightPool:
    def __init__(self, max_browsers=1, max_pages_per_browser=1,executable_path=None):
        self.max_browsers = max_browsers
        self.max_pages = max_pages_per_browser
        self.executable_path = executable_path
        self._browser_wrappers:list[PlayWrightWrapper]=[]
        self._plugins_cycle = None

    async def init_pool(self,playwright, browser_type):
        try:
            #playwright = await async_playwright().start() 
            for i in range(self.max_browsers):
                browser_wrapper = PlayWrightWrapper(playwright,browser_type,i,self.max_pages,executable_path = self.executable_path)
                await browser_wrapper.init_wrapper()
                self._browser_wrappers.append(browser_wrapper)
            self._plugins_cycle = itertools.cycle(self._browser_wrappers)
        except Exception as e:
            KobaLogger.logger_koba.error(f"{browser_type} pool init fail: {e}")
            raise e
    
    async def get_browser_wrapper_and_context(self):
        while True:
            try:
                browserWrapper = next(self._plugins_cycle)
                #context = await asyncio.wait_for(browserWrapper.get_context(), timeout=0.1)
                context = await browserWrapper.get_context()
                #context = await browserWrapper.get_context_no_wait()
                return browserWrapper,context
            except:
                continue


    async def clean_async(self):
        for browser_wrapper in self._browser_wrappers:
            context = browser_wrapper.context
            browser = browser_wrapper.browser
            playwright = browser_wrapper.playwright
            await context.close()
            await browser.close()
            await playwright.stop()

                