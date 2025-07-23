# 创建文件处理器
import logging
import os
from modules.utils.koba_logger import KobaLogger

# os.makedirs('logs/svs_plugins', exist_ok=True)
# file_handler = logging.FileHandler('logs/svs_plugins/selenium_log.log', mode='a')
# file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# # 创建控制台处理器
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# logging.basicConfig(
#     level=logging.INFO,
#     handlers=[file_handler, console_handler]
# )

# selenium_logger=logging.getLogger('selenium')
k=KobaLogger()
fetch_logger=KobaLogger.logger_koba