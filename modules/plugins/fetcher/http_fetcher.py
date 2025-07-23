import time

import requests
from modules.plugins.fetcher.common.fetch_context import FetchContext
from modules.plugins.fetcher.common.fetch_util import get_text_v2
from .common.s_logging import fetch_logger

class HttpFetcher:
    def __init__(self, context: FetchContext):
        self.context = context

    def fetch(self,timeout=(1,3))->FetchContext:
        url =self.context.url
        try:
            err = None
            html = "NA"
            request_complete = None
            starttime = time.time()
            fetch_logger.info(f"start request {url}")
            res = requests.get(url,timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
                        "Connection": "keep-alive"}
                )
            request_complete = time.time()
            if res.status_code == 200:
                content_type = res.headers.get("Content-Type")
                if content_type and "text/html" not in content_type:
                    err = "not html"
                if res.encoding == "ISO-8859-1":
                    content = res.content
                    html = content.decode("utf-8")
                else:
                    html = res.text            
            else:
                fetch_logger.info(f"get html {url} by request failed,status code: {res.status_code}")
                err = f"{res.status_code}"
        except requests.exceptions.ReadTimeout:
            fetch_logger.info(f"get html {url} by http read timeout")
            err = "read timeout"
        except requests.exceptions.ConnectTimeout:
            fetch_logger.info(f"get html {url} by http connect timeout")
            err = "connect timeout" 
        except Exception as e:
            fetch_logger.info(f"get html {url} by request fail: {e}")
            err = "error"
            if("Network is unreachable" in str(e)):
                err = "unreachable" 
        finally:
            if request_complete:
                fetch_logger.info(f"get html {url} by request complete: {request_complete - starttime}s,encode cost {time.time()-request_complete}s")
            else:
                fetch_logger.info(f"get html {url} by request complete: {time.time() - starttime}")
            
            self.context.status.http_err = err
            self.context.response.http_html = html
            return self.context
        
        
    def need_use_browser(self) -> bool:
        url = self.context.url
        err = self.context.status.http_err
        html = self.context.response.http_html

        if err and err not in ["unreachable","connect timeout"]:
            return True
        
        ss = time.time()
        len_html = len(html)
        html_text = get_text_v2(html)
        len_text = len(html_text)
        fetch_logger.info(f"{url} get text : {time.time()-ss}s  {len_html}->{len_text}")
        if len_text<1024:
            fetch_logger.info(f"{url} html too short,use broswer")
            return True
        
        return False