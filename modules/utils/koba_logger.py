import logging
import os
from logging.handlers import RotatingFileHandler

from .config import PROJECT_ROOT


class KobaLogger:
    _instance = None
    _logger = None
    logger_koba: 'KobaLogger'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialize_logger()
            cls.logger_koba = cls._instance  # 保证 koba_logger 被设置为创建的实例
        return cls._instance

    @classmethod
    def _initialize_logger(cls):
        """初始化logger配置"""
        print(" * 初始化 KobaLogger...")
        # 创建日志目录
        # log_dir = os.path.join(PROJECT_ROOT, "logs", "svs_plugins")
        log_dir = os.path.join(os.path.dirname(PROJECT_ROOT), "logs", "svs_plugins")
        os.makedirs(log_dir, exist_ok=True)

        # 设置日志文件路径
        log_file = os.path.join(log_dir, "svs_plugins.log")

        # 创建logger
        logger = logging.getLogger("svs_plugins")
        logger.setLevel(logging.INFO)

        # 如果logger已经有handlers，先清除
        if logger.handlers:
            logger.handlers.clear()

        # 创建文件处理器
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=2 * 1024 * 1024,  # 2MB
            backupCount=5,
            encoding='utf-8'
        )

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # 确保控制台输出级别为 INFO

        # 设置日志格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # 避免日志传递到父logger
        logger.propagate = False

        cls._logger = logger

    @classmethod
    def info(cls, msg, *args, **kwargs):
        if cls._logger is None:
            cls._initialize_logger()
        if cls._logger is None:
            raise RuntimeError("Logger not initialized")
        cls._logger.info(msg, *args, **kwargs)

    @classmethod
    def error(cls, msg, *args, **kwargs):
        if cls._logger is None:
            cls._initialize_logger()
        if cls._logger is None:
            raise RuntimeError("Logger not initialized")
        cls._logger.error(msg, *args, **kwargs)

    @classmethod
    def warning(cls, msg, *args, **kwargs):
        if cls._logger is None:
            cls._initialize_logger()
        if cls._logger is None:
            raise RuntimeError("Logger not initialized")
        cls._logger.warning(msg, *args, **kwargs)

    @classmethod
    def debug(cls, msg, *args, **kwargs):
        if cls._logger is None:
            cls._initialize_logger()
        if cls._logger is None:
            raise RuntimeError("Logger not initialized")
        cls._logger.debug(msg, *args, **kwargs)


# 创建全局logger实例
# logger = KobaLogger()

# 为了向后兼容，保留原来的命名
# logger_koba = logger

# def get_logger():
#     """
#     返回单例的 KobaLogger 实例。主进程入口处先调用一次以完成初始化。
#     """
#     return KobaLogger()
