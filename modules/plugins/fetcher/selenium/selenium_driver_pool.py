import queue
from .selenium_driver import SeleniumDriver
from ..common.s_logging import fetch_logger
class SeleniumDriverPool:
    def __init__(self,url=None,size=1,type="driver",uc=False,page_load_strategy="eager",executable_path="/opt/ungooled-chromium/chrome"):
        """初始化指定数量的 WebDriver 实例"""
        self.drivers = queue.Queue(maxsize=size)
        if url is not None:
            colon_index = url.find(':')
            ip = url[:colon_index]
            port = url[colon_index + 1:url.find('/', colon_index)]
            fetch_logger.info(f"IP: {ip}")
            fetch_logger.info(f"Port: {port}")
        else:
            ip = None
            port = None
        for i in range(size):
            if(type=="driver"):
                driver =SeleniumDriver(ip,port,number=i,uc=uc,page_load_strategy=page_load_strategy,binary_location=executable_path)         
            self.drivers.put(driver)
    
    def acquire(self):
        """获取一个可用 WebDriver（阻塞直到有可用实例）"""
        return self.drivers.get()
    
    def release(self, driver):
        """释放 WebDriver 回池中"""
        driver.reinit()
        self.drivers.put(driver)
    
    def close_all(self):
        """关闭所有 WebDriver 实例"""
        while not self.drivers.empty():
            driver = self.drivers.get()
            driver.cleanup()