from ..common.s_logging import fetch_logger
import sys
import time
from seleniumbase import Driver

from ..common.fetch_util import check_html, clean_md, get_text_v2
from markdownify import markdownify as md


class SeleniumDriver():
    def __init__(self, servername=None,port=None,number=-1,uc=False,page_load_strategy="none",binary_location="/opt/ungooled-chromium/chrome"):
        try:        
            self.servername=servername,
            self.port=port
            self.isWorking=False
            self.number=number
            self.uc = uc
            self.page_load_strategy=page_load_strategy  
            self.binary_location=binary_location  
            self.init_driver()       
            self.isInit=True
        except Exception as e:
            raise e
        
    def __del__ (self):
       self.cleanup()     

    def init_driver(self):
        if self.servername and self.port:
            self.driver=Driver(
                headed=True,
                servername=self.servername,
                port=self.port,
                disable_js = False,
                block_images=True,
                page_load_strategy=self.page_load_strategy,
            )
        else:
            self.driver=Driver(
                headless1=True,
                headed=False,
                uc=self.uc,
                page_load_strategy=self.page_load_strategy,
                disable_js = False,
                block_images=True,
                locale_code="en-US",
                incognito=True,
                binary_location=self.binary_location
            )
        #self.driver.unhandled_prompt_behavior = 'accept'
        self.driver.set_page_load_timeout(30)  # 页面加载超时（秒）
        self.driver.set_script_timeout(20)     # 脚本执行超时
        self.driver.implicitly_wait(10)        # 隐式等待（元素查找）

    def check_driver_health(self):
        try:
            self.driver.get_title()
        except Exception as e:
            fetch_logger.info(f"check driver {self.number} health fail: {e}")
            self.cleanup()
            self.init_driver()
            self.isInit=True

    def reinit(self):
        try:
            self.isInit=False
            if self.driver:
                self.driver.quit()
            self.init_driver()
            self.isInit=True
            fetch_logger.info("driver %s reinit",self.number)
        except Exception as e:
            fetch_logger.error("driver %s Failed to reinit driver: %s",self.number, e)
    def cleanup(self):
        try:
            if self.driver:
                self.driver.quit()   
                fetch_logger.info("driver %s quit",self.number)          
        except Exception as e:
            fetch_logger.error("driver %s Failed to quit driver: %s",self.number, e)
        finally:
            self.driver = None
            self.isInit=False

    def get_html(self,url,delay=3):
        if (self.isInit==False):
            fetch_logger.warning("driver %s is not init",self.number)
            self.reinit()
        self.check_driver_health()
        if self.uc:
            if self.page_load_strategy=="none":
                return self.get_html_uc_none(url)
            else:
                return self.get_html_uc_eager(url)
        else:
            return self.get_html_normal(url,delay)
        

    def get_html_uc_none(self,url,delay=3):
        try:
            fetch_logger.info(f"uc driver {self.number} start get_html {url}")
            start_time = time.time()
            self.driver.uc_open_with_reconnect(url, 2)   
            #self.driver.uc_activate_cdp_mode(url)
            #self.driver.get(url) 
            # cur_url=self.driver.get_current_url()      
            # if cur_url != url:
            #     selenium_logger.error(f"uc driver {self.number} Failed to get HTML: {cur_url} not match")
            #     return "Network is unreachable"
            html = self.driver.get_page_source()
            get_complete = time.time()   
            if len(html)>64 and not check_html(url,html):
                fetch_logger.error(f"uc driver {self.number} html check fail")
                return None      
            len_list=[len(html)]
            while True:
                time.sleep(0.2)
                new_html = self.driver.get_page_source()
                html_len = len(html)
                new_html_len = len(new_html)
                if(new_html_len<html_len):
                    new_html_len = html_len
                diff = new_html_len - html_len
                threshold = 128 if html_len*0.1 < 128 else html_len*0.1
                len_list.append(new_html_len)
                html = new_html
                cost = time.time() - get_complete
                if new_html_len>64 and not check_html(url,html):
                    fetch_logger.error(f"uc driver {self.number} html check fail")
                    html=None
                    break
                if cost > 1 and self.driver.get_current_url() == "about:blank":
                    fetch_logger.error(f"uc driver {self.number} cur url is about:blank")
                    html=None
                    break
                if (new_html_len>1024 and diff<threshold) or cost>delay:
                    break                         
            len_list_str = "->".join(map(str, len_list))
            #self.driver.save_screenshot("save.png")
            fetch_logger.info(f"uc driver {self.number} get_html {url} length changes: {len_list_str}")
            end_time = time.time()
            fetch_logger.info(f"uc driver {self.number} get_html {url} time: {get_complete - start_time}s  {end_time - get_complete}s")           
            return html
        except Exception as e:
            fetch_logger.error(f"uc driver {self.number} Failed to get url {url}: %s", e)
            #self.check_driver_health()
            return None
        finally:
            self.driver.get("about:blank")
            
        
    def get_html_uc_none_V2(self,url):
        try:
            fetch_logger.info(f"uc driver {self.number} start get_html {url}")
            start_time = time.time()
            #self.driver.get(url)
            self.driver.uc_open_with_reconnect(url, 2)     
            html = self.driver.get_page_source()
            print(len(get_text_v2(html)))  
            s2 = time.time()     
            try:
                self.driver.assert_non_empty_text(selector="body",timeout=3)
            except Exception as e:
                fetch_logger.error(f"driver {self.number} Failed to get HTML: %s", e)
                return "Network is unreachable"
            if self.driver.get_current_url() != url:
                fetch_logger.error("uc driver %s Failed to get HTML: %s", self.number, "url not match")
                return "Network is unreachable"
            html = self.driver.get_page_source()   
            print(len(get_text_v2(html)))        
            if(html is None or len(html)==0):
                e = Exception("HTML is empty")
                fetch_logger.error(f"uc driver {self.number} Failed to get HTML: %s", e)
                raise e
            end_time = time.time()
            fetch_logger.info(f"uc driver {self.number} get_html {url} success,cost {s2-start_time}s {end_time - s2}s")
            return html
        except Exception as e:
            fetch_logger.error(f"uc driver {self.number} Failed to get HTML: %s", e)
            raise e

    def get_html_uc_eager(self,url):
        try:
            fetch_logger.info(f"uc driver {self.number} start get_html {url}")
            start_time = time.time()
            self.driver.uc_open_with_reconnect(url, 3)
            html = self.driver.get_page_source()
            print(len(get_text_v2(html)))
            if(html is None or len(html)==0):
                e = Exception("HTML is empty")
                fetch_logger.error(f"uc driver {self.number} Failed to get HTML: %s", e)
                raise 
            end_time = time.time()
            fetch_logger.info(f"uc driver {self.number} get_html {url} success,cost {end_time - start_time}s")
            return html
        except Exception as e:
            fetch_logger.error(f"uc driver {self.number} Failed to get HTML: %s", e)
            raise e
        
    def get_html_normal(self,url,delay=5000):
        try:
            fetch_logger.info(f"driver {self.number} start get_html {url}")
            start_time = time.time()
            #self.driver.get(url)
            self.driver.get(url)
            try:
                self.driver.assert_non_empty_text(selector="body",timeout=5)
            except Exception as e:
                fetch_logger.error(f"driver {self.number} Failed to get HTML: %s", e)
                return "Network is unreachable"
            html = self.driver.get_page_source()
            if(html is None or len(html)==0):
                e = Exception("HTML is empty")
                fetch_logger.error(f"driver {self.number} Failed to get HTML: %s", e)
                raise e           
            num =0
            len_list=[len(get_text_v2(html))]
            while True:
                time.sleep(0.5)
                num += 1
                new_html = self.driver.get_page_source()
                html_len = len(get_text_v2(html))
                new_html_len = len(get_text_v2(new_html))
                diff = new_html_len - html_len
                threshold = 128 if html_len*0.1 < 128 else html_len*0.1
                len_list.append(new_html_len)
                if (new_html_len>128 and diff<threshold) or num*500>delay:
                    break
                html = new_html
            end_time = time.time()
            fetch_logger.info(f"driver {self.number} get_html {url} success,cost {end_time - start_time}s")
            len_list_str = "->".join(map(str, len_list))
            fetch_logger.info(f"driver {self.number} get_html {url} length changes: {len_list_str}")
            self.driver.save_screenshot("save.png")
            return html
        except Exception as e:
            fetch_logger.error(f"driver {self.number} Failed to get HTML: %s", e)
            raise e
        

