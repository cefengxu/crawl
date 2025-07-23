from concurrent.futures import ThreadPoolExecutor
import re
import threading
import time
from html2text import html2text
from markdownify import markdownify as md
from trafilatura import extract,extract_metadata,html2txt

from modules.plugins.fetcher.common.fetch_context import FetchContext
from modules.plugins.fetcher.common.fetch_util import *
from .s_logging import fetch_logger

class FetchParser():
    def __init__(self,context:FetchContext):
        self.context = context

    def parse(self,parser_type=None):
        if parser_type is None:
            parser_type = self.context.option.parse_type

        if not self.check_html():
            return self.context
        
        if parser_type == "sum_v2":
            self.html_to_md_sum_V2()
        elif parser_type == "sum":
            self.html_to_md_sum()
        elif parser_type == "normal":
            self.html_to_md_normal()
        else:
            fetch_logger.error(f"parser_type {parser_type} is not support")
        
        return self.context

    # def html_to_md_sum_V2(self,re=False):
    #     try:
    #         if self.context.response.sum_md_tr != "NA" and re!=True:
    #             return
    #         start1=time.time()  
    #         html = self.context.response.html     
    #         url = self.context.url              
    #         sum_md = sum_html_trafilatura(html)
    #         if sum_md is None:
    #             fetch_logger.warning(f"{url} sum_md is None")
    #             sum_md = get_md(html)
    #         elif len(sum_md)<1024:                
    #             all_md = get_md(html)
    #             if len(sum_md)<len(all_md)/3:
    #                 fetch_logger.warning(f"{url} sum_md is too short: {len(sum_md)}")
    #                 sum_md=all_md
    #         fetch_logger.info(f" {url} html to md trafilatura cost: {time.time() - start1:.4f} seconds")       
    #         self.context.response.sum_md_tr = sum_md
    #         self.context.response.final_md = sum_md
    #     except Exception as e:
    #         fetch_logger.error(f"{url} html sum to md fail: {e}")
    #         self.context.status.status = "sum error"
    #         self.context.status.msg = str(e)

    def html_to_md_sum_V2(self,re=False):
        try:
            if self.context.response.sum_md_tr != "NA" and re!=True:
                return
            start1=time.time()  
            html = self.context.response.html     
            url = self.context.url              

            with ThreadPoolExecutor() as executor:
                sum_future = executor.submit(sum_html_trafilatura,html)
                md_future = executor.submit(get_md,html)
            
            sum_md = sum_future.result()
            self.context.response.sum_md_tr = sum_md
            md = md_future.result()
            self.context.response.md  = md

            final_md = "NA"
            if sum_md is None or sum_md =="":
                final_md = md  
            elif len(sum_md)<len(md)/5:
                fetch_logger.warning(f"{url} sum_md is too short: {len(sum_md)}")
                final_md = md
            else:
                final_md = sum_md

            fetch_logger.info(f" {url} html to md trafilatura cost: {time.time() - start1:.4f} seconds")       
            self.context.response.final_md = final_md
        except Exception as e:
            fetch_logger.error(f"{url} html sum to md fail: {e}")
            self.context.status.status = "sum error"
            self.context.status.msg = str(e)
    
    def html_to_md_sum(self,re=False):
        try:
            if self.context.response.sum_md_re != "NA" and re!=True:
                return
            start1=time.time()   
            html = self.context.response.html     
            url = self.context.url                  
            sum_html,title = sum_html_readabilipy(html)
            sum_md = get_md(sum_html)
            fetch_logger.info(f" {url} html to md cost: {time.time() - start1:.4f} seconds")          
            self.context.response.sum_md_re = sum_md
            self.context.response.title = title
            self.context.response.final_md = sum_md
        except Exception as e:
            fetch_logger.error(f"{url} html sum to md fail: {e}")
            self.context.status.status = "sum error"
            self.context.status.msg = str(e)
        
    def html_to_md_normal(self,re=False):
        try:
            if self.context.response.md != "NA" and re!=True:
                return
            start1=time.time()    
            html = self.context.response.html     
            url = self.context.url        
            c_md = get_md(html)
            fetch_logger.info(f" {url} html to md cost: {time.time() - start1:.4f} seconds")           
            self.context.response.md = c_md
            self.context.response.final_md = c_md
        except Exception as e:
            fetch_logger.error(f"{url} html to md fail: {e}")
            self.context.status.status = "md error"
            self.context.status.msg = str(e)


    def save_responce(self,file_type,parse_type=None,add_url = False):   

        if file_type not in ["html","md"]:
            fetch_logger.error(f"{self.url} save file fail: file_type error")
            return
        
        if parse_type is None:
            parse_type = self.context.option.parse_type

        if file_type == "html":
            context = self.context.response.html
        elif file_type == "md":
            if parse_type == "normal":
                context = self.context.response.md
            elif parse_type == "sum":
                context = self.context.response.sum_md_re
            elif parse_type == "sum_V2":
                context = self.context.response.sum_md_tr
            else:
                fetch_logger.error(f"parse_type {parse_type} not support")
            
        
        if context is None or context == "":
            fetch_logger.error(f"{self.url} save file fail: html is None")
            return
        
        if add_url:
            url = self.context.url
            context = f"{url}\n\n{context}"
        
        timestamp = time.localtime(time.time())
        formatted_datetime_dir = time.strftime("%Y-%m-%d", timestamp)
        formatted_datetime = time.strftime("%H:%M:%S", timestamp)

        title = self.context.response.title
        filename = f"{title}_{formatted_datetime}_{parse_type}.{context}"
        directory = os.path.join(os.path.dirname(__file__), "storage", file_type, formatted_datetime_dir)
        full_path = os.path.join(directory, filename)

        save_file(context, full_path)

    def check_html(self):
        html = self.context.response.html
        url = self.context.url
        if html == "NA" or html == "":
            fetch_logger.error(f"{url} html is empty")
            self.context.status.status = "error page"
            self.context.status.msg = "html is empty"
        elif "403 Forbidden" in html:
            fetch_logger.error(f"{url} html is 403 Forbidden")
            self.context.status.status = "error page"
            self.context.status.msg = "html is 403 Forbidden"
            return False
        elif "Verifying you are human" in html:
            fetch_logger.error(f"{url} html is Verifying you are human")
            self.context.status.status = "error page"
            self.context.status.msg = "html is Verifying you are human"
            return False
        elif "不支持安全链接" in html:
            fetch_logger.error(f"{url} html is 不支持安全链接")
            self.context.status.status = "error page"
            self.context.status.msg = "html is 不支持安全链接"
            return False
        elif "404 Not Found" in html:
            fetch_logger.error(f"{url} html is 404 Not Found")
            self.context.status.status = "error page"
            self.context.status.msg = "html is 404 Not Found"
            return False
        return True