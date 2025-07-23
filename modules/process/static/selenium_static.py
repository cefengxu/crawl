import time
from .base_static import BaseStatic
from ...plugins.fetcher.common.fetch_context import FetchContext
import asyncio
from ...plugins.fetcher.selenium.selenium_manage import SeleniumManage
from modules.utils.config import Config

class SeleniumStatic(BaseStatic):
    def __init__(self):
        super().__init__()
        c = Config()
        browser_num = Config.app_config.plugins.fetcher.selenium.browser_num
        exec_path = Config.app_config.plugins.fetcher.selenium.browser_path
        self.selenium = SeleniumManage(browser_num,executable_path=exec_path,uc=True)
        
    async def fetch_selenium(self, context: FetchContext) -> FetchContext:
        loop = asyncio.get_running_loop()
        html,err = await loop.run_in_executor(None, SeleniumManage().get_html, context.url)
        if err:
            context.status.status = err
        else:
            context.response.browser_html = html
        return context
        