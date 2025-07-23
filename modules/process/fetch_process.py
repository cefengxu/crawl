import random
from threading import Thread
from modules.plugins.fetcher.common.fetch_util import save_context
from modules.plugins.fetcher.http_fetcher import HttpFetcher
from .base_process import BaseProcess
import asyncio
import time
from ..plugins.base_request_model import FetchModel
from ..plugins.fetcher.common.fetch_context import FetchContext, FetchOptionContext
from ..plugins.fetcher.common.fetch_parser import FetchParser
from modules.utils.koba_logger import KobaLogger
# from modules.utils.verify import verify
# from ..plugin.selenium_fetcher.myselenium.selenium_manage import SeleniumManage

class FetchProcess(BaseProcess):
    def __init__(self, item: FetchModel):
        self.url = item.url
        self.parser = item.parser
        self.fetch_engine = item.fetch_engine
        self.info = item.info
        self.params = item.params
        self.task_id = item.task_id
        self.key = item.key
        
    def fetch_browser(self, context: FetchContext, static_manager: dict[str, list]):
        try:
            start = time.time()
            fetch_type = context.option.fetch_type
            playwright_process_num = len(static_manager.get("playwright"))
            #print(f"playwright_process_num: {playwright_process_num}")
            playwright_index = random.randint(0, playwright_process_num-1)
            #KobaLogger.logger_koba.info(f"use playwright {playwright_index}")
            handlers = {
                "pl_chrome": static_manager.get("playwright")[playwright_index].fetch_playwright_chrome,
                "pl_chrome_doc": static_manager.get("playwright")[playwright_index].fetch_playwright_chrome_doc,
                "pl_chrome_load": static_manager.get("playwright")[playwright_index].fetch_playwright_chrome_load,
                # "pl_camoufox": static_manager.get("playwright")[playwright_index].fetch_playwright_camoufox,
                # "pl_camoufox_doc": static_manager.get("playwright")[playwright_index].fetch_playwright_camoufox_doc,
                "selenium": static_manager.get("selenium")[0].fetch_selenium,
            }
            handler = handlers.get(fetch_type)
            if handler is not None:
                context = handler(context).result()            
        finally:
            context.pipeline.broswer_time  = (time.time() - start)*1000
            return context
        

    def fetch_auto(self, context: FetchContext, static_manager: dict[str, list]) -> FetchContext:
        http_request_start = time.time()
        http_fetcher = HttpFetcher(context)
        context = http_fetcher.fetch()
        context.pipeline.http_time = (time.time() - http_request_start)*1000
        if http_fetcher.need_use_browser():
            context = self.fetch_browser(context, static_manager) 
            if context.status.http_err:
                context.response.html = context.response.browser_html
            else:
                len_http_html = len(context.response.http_html)
                len_browser_html = len(context.response.browser_html)

                if len_http_html > len_browser_html:
                    context.response.html = context.response.http_html
                    context.status.final_use_fetcher = "http"
                else:
                    context.response.html = context.response.browser_html
        else:
            context.status.final_use_fetcher = "http"
            if context.status.http_err:
                context.response.html = "NA" 
                context.response.final_md  = "NA"
                context.status.status = context.status.http_err
                return              
            context.response.html = context.response.http_html
        return context
    
    def fetch_http(self, context: FetchContext) -> FetchContext:
        http_request_start = time.time()
        http_fetcher = HttpFetcher(context)
        context = http_fetcher.fetch(timeout=(10,10))
        context.pipeline.http_time = (time.time() - http_request_start)*1000
        context.response.html = context.response.http_html
        return context

    def fetch_browser_only(self, context: FetchContext, static_manager: dict[str, list]) -> FetchContext:
        context = self.fetch_browser(context, static_manager) 
        context.response.html = context.response.browser_html
        return context

    async def process(self, static_manager: dict[str, list] = {}):
        KobaLogger.info(f"⏳开始爬取: {self.url} ⏳")
        
        start_time = time.time()
        # manage = SeleniumManage(3,uc=True)
        # html = manage.get_html(self.url)
        # await asyncio.sleep(2)
        
        try:
            context = FetchContext(
                url = self.url,
                taskid = self.task_id,
                option = FetchOptionContext(
                    fetch_type = self.fetch_engine,
                    parse_type = self.parser,
                )
                
            )
            context.status.final_use_fetcher = self.fetch_engine

            # if self.key!="" and not verify(self.key):
            #     context.status.status = "verify fail"
            #     raise Exception("verify fail")

            if context.option.fetch_type == "http":
                context = self.fetch_http(context)
            elif self.params.browser_only:
                context = self.fetch_browser_only(context,static_manager)
            else:
                context = self.fetch_auto(context,static_manager)

            if context.status.status == "success":                             
                parse_start = time.time()
                parser = FetchParser(context)
                parser.parse()
                context.pipeline.parser_time = (time.time() - parse_start)*1000

        except Exception as e:
            # logger_koba.error(f"{url} fetch fail: {e}")
            if context.status.status == "success":
                context.status.status = "fetch error"
                context.status.msg = str(e)
        finally:
            if self.params.context_cache:
                Thread(target=save_context, args=(context,)).start()
                #save_context(context)
            if  context.status.status == "success" and (context.response.final_md == "NA" or context.response.final_md == ""):
                context.status.status = "empty"
            context.pipeline.complete_time = (time.time() - start_time)*1000
            context.response.md_length  = len(context.response.final_md)
        
        
        end_time = time.time()
        KobaLogger.info(f"⏳ {self.url} 检索总耗时:{(end_time - start_time)} 秒,文本长度:{len(context.response.final_md)}")
        # SeleniumManage.clear_all_driver()
        return { 'times': (end_time - start_time), 'results': context}