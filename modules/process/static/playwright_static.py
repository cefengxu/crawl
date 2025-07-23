import time
from modules.plugins.fetcher.playwright.playwright_manage import PlayWrightManager
from .base_static import BaseStatic
from ...plugins.fetcher.common.fetch_context import FetchContext
from modules.utils.config import Config
class PlaywrightStatic(BaseStatic):
    def __init__(self):
        super().__init__()
        c = Config()
        page_num = Config.app_config.plugins.fetcher.playwright.page_num
        browser_num = Config.app_config.plugins.fetcher.playwright.browser_num
        exec_path = Config.app_config.plugins.fetcher.playwright.browser_path
        self.playwright = PlayWrightManager(browser_num,page_num,False,executable_path=exec_path)
        
    async def fetch_playwright_chrome(self, context: FetchContext) -> FetchContext:
        async with await PlayWrightManager().create() as fetcher:            
            context = await fetcher.fetch_queue_and_wait(context,"commit","chrome")
            return context
        
    async def fetch_playwright_chrome_doc(self, context: FetchContext) -> FetchContext:
        async with await PlayWrightManager().create() as fetcher:            
            context = await fetcher.fetch_queue_and_wait(context,"domcontentloaded","chrome")
            return context
        
    async def fetch_playwright_chrome_load(self, context: FetchContext) -> FetchContext:
        async with await PlayWrightManager().create() as fetcher:            
            context = await fetcher.fetch_queue_and_wait(context,"load","chrome")
            return context
        