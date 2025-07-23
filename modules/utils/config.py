# 修改导入部分
import os
import threading
from pathlib import Path
from typing import Dict, Optional

import yaml  # 替换 tomllib
from pydantic import BaseModel, Field


def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).resolve().parent.parent.parent


PROJECT_ROOT = get_project_root()
WORKSPACE_ROOT = os.path.join(os.path.dirname(PROJECT_ROOT), "workspace")


class LLMSettings(BaseModel):
    model: str = Field(..., description="Model name")
    host: str = Field(..., description="API host")
    port: int = Field(..., description="API port")
    api: str = Field(..., description="API endpoint")
    api_key: str = Field(..., description="API key")
    max_tokens: int = Field(4096, description="Maximum number of tokens per request")
    temperature: float = Field(0.2, description="Sampling temperature")
    enable: bool = Field(False, description="Whether the model is available")


class MLMSettings(BaseModel):
    model: str = Field(..., description="Model name")
    host: str = Field(..., description="API host")
    port: int = Field(..., description="API port")
    api: str = Field(..., description="API endpoint")
    api_key: str = Field(..., description="API key")
    max_tokens: int = Field(4096, description="Maximum number of tokens per request")
    max_image_tokens: int = Field(6192, description="Maximum image tokens to use")
    temperature: float = Field(0.2, description="Sampling temperature")
    enable: bool = Field(True, description="Whether the model is available")


class ConsulSettings(BaseModel):
    host: str = Field(..., description="Consul host address")
    port: int = Field(..., description="Consul port")
    interval: str = Field(..., description="Consul interval")


class ServiceSettings(BaseModel):
    port: int = Field(..., description="Service port")
    # tmp_directory: str = Field(default=os.path.dirname(PROJECT_ROOT) , description="temp directory for file saving.")
    tmp_directory: str = Field(default=WORKSPACE_ROOT, description="temp directory for file saving.")
    device: str = Field(default="cuda:0", description="cuda device be used")
    cpu_core_num: int = Field(4, description="Number of CPU cores to use")

    def __init__(self, **data):
        super().__init__(**data)
        # 确保临时目录存在
        if not os.path.exists(self.tmp_directory):
            os.makedirs(self.tmp_directory, exist_ok=True)


# class OCRSettings(BaseModel):
#     host: str = Field("http://127.0.0.1", description="OCR service host")
#     port: int = Field(9402, description="OCR service port")
#     api: str = Field("/api/v1/models/ocr", description="OCR API endpoint")

# class FormulaRecSettings(BaseModel):
#     host: str = Field("http://10.176.238.83", description="Formula recognition service host")
#     port: int = Field(9402, description="Formula recognition service port")
#     api: str = Field("/api/v1/models/formularec", description="Formula recognition API endpoint")
#     enable: bool = Field(False, description="Whether to enable formula recognition")

# class TokenizerSettings(BaseModel):
#     host: str = Field("http://127.0.0.1", description="Tokenizer service host")
#     port: int = Field(9402, description="Tokenizer service port")
#     api: str = Field("/api/v1/models/tokenizer", description="Tokenizer API endpoint")

# class ChunkSettings(BaseModel):
#     chunk_size: int = Field(512, description="Chunk size")
#     chunk_overlap: int = Field(64, description="Chunk overlap")
#     graph_chunk_size: int = Field(1200, description="Chunk size of Graph")
#     graph_chunk_overlap: int = Field(100, description="Chunk overlap of Graph")


# class PromptSettings(BaseModel):
#     slide_zh: str = Field(..., description="System prompt")
#     slide_ocr_zh: str = Field(..., description="History prompts")
#     slide_en: str = Field(..., description="Maximum number of history prompts")
#     slide_ocr_en: str = Field(..., description="System prompt")
#     image_to_text_zh: str = Field(..., description="History prompts")
#     image_to_text_ocr_zh: str = Field(..., description="Maximum number of history prompts")
#     image_to_text_en: str = Field(..., description="System prompt")
#     image_to_text_ocr_en: str = Field(..., description="History prompts")
#     chunk_analysis_en: str = Field(..., description="Maximum number of history prompts")
#     chunk_analysis_zh: str = Field(..., description="System prompt")
#     chunk_analysis_with_image_en:str = Field(..., description="History prompts")
#     chunk_analysis_with_image_zh: str = Field(..., description="Maximum number of history prompts")


# class SearchPluginSettings(BaseModel):
#     enabled: bool = Field(False, description="Whether search plugin is enabled")
#     model_name: str = Field(..., description="Search model name")
#     subscription_key: str = Field(..., description="API subscription key")
#     endpoint: str = Field(..., description="API endpoint")

class SeleniumPluginSettings(BaseModel):
    browser_num: int = Field(default=1, description="Number of browsers")
    browser_path: str = Field(default="/opt/ungoogled-chromium/chrome", description="Path to browser executable")

class PlaywrightPluginSettings(BaseModel):
    page_num: int = Field(default=1, description="Number of pages")
    browser_num: int = Field(default=1, description="Number of browsers")
    process_num: int = Field(default=1, description="Number of processes")
    browser_path: str = Field(default="/opt/ungoogled-chromium/chrome", description="Path to browser executable")

class FetcherPluginSettings(BaseModel):
    enabled: bool = Field(False, description="Whether fetcher plugin is enabled")
    selenium: Optional[SeleniumPluginSettings] = Field(default_factory=lambda: SeleniumPluginSettings(), description="Settings for selenium plugin")
    playwright: Optional[PlaywrightPluginSettings] = Field(default_factory=lambda: PlaywrightPluginSettings(), description="Settings for playwright plugin")


class SearchProviderSettings(BaseModel):
    subscription_key: str = Field(..., description="API subscription key")
    endpoint: str = Field(..., description="API endpoint")


class SearchPluginV2Settings(BaseModel):
    enabled: bool = Field(False, description="Whether search plugin is enabled")
    searchers: Dict[str, SearchProviderSettings] = Field(
        default_factory=dict,
        description="Dictionary of search providers configurations"
    )


class WeatherPluginSettings(BaseModel):
    enabled: bool = Field(False, description="Whether weather plugin is enabled")
    subscription_key: str = Field(..., description="API subscription key")
    endpoint_weather: str = Field(..., description="Weather API endpoint")
    endpoint_forecast: str = Field(..., description="Forecast API endpoint")


class PluginSettings(BaseModel):
    # search: Optional[SearchPluginSettings] = None
    fetcher:Optional[FetcherPluginSettings] = None
    search: Optional[SearchPluginV2Settings] = None
    weather: Optional[WeatherPluginSettings] = None


class SeleniumSettings(BaseModel):
    browser_nums: int = Field(5, description="Number of browser instances to maintain in the pool")


class CentSvsSettings(BaseModel):
    host: str = Field(..., description="Central service host")
    port: int = Field(..., description="Central service port")


class AppConfig(BaseModel):
    llm: Dict[str, LLMSettings]
    mlm: Dict[str, MLMSettings]
    consul: ConsulSettings
    service: ServiceSettings
    plugins: Optional[PluginSettings] = None
    selenium: Optional[SeleniumSettings] = None
    cent_svs: CentSvsSettings  # 新增的配置项

    class Config:
        arbitrary_types_allowed = True


class Config:
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    app_config: 'Config'

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls.app_config = cls._instance
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    self._load_initial_config()
                    self._initialized = True

    @staticmethod
    def _get_config_path() -> Path:
        root = PROJECT_ROOT
        config_path = root / "config.yaml"
        if config_path.exists():
            return config_path
        example_path = root / "config" / "config.example.toml"
        if example_path.exists():
            return example_path
        raise FileNotFoundError("No configuration file found in config directory")

    def _load_config(self) -> dict:
        config_path = self._get_config_path()
        with config_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_initial_config(self):
        print(" * 初始化配置...")
        raw_config = self._load_config()

        # LLM 配置
        base_llm = raw_config.get("llm", {})
        llm_overrides = {
            k: v for k, v in raw_config.get("llm", {}).items() if isinstance(v, dict)
        }

        llm_default_settings = {
            "model": base_llm.get("model"),
            "host": base_llm.get("host"),
            "port": base_llm.get("port"),
            "api": base_llm.get("api"),
            "api_key": base_llm.get("api_key"),
            "max_tokens": base_llm.get("max_tokens", 4096),
            "temperature": base_llm.get("temperature", 0.2),
            "enable": base_llm.get("enable", False),
        }

        # MLM 配置
        base_mlm = raw_config.get("mlm", {})
        mlm_overrides = {
            k: v for k, v in raw_config.get("mlm", {}).items() if isinstance(v, dict)
        }
        
        mlm_default_settings = {
            "model": base_mlm.get("model"),
            "host": base_mlm.get("host"),
            "port": base_mlm.get("port"),
            "api": base_mlm.get("api"),
            "api_key": base_mlm.get("api_key"),
            "max_tokens": base_mlm.get("max_tokens", 4096),
            "max_image_tokens": base_mlm.get("max_image_tokens", 6192),
            "temperature": base_mlm.get("temperature", 0.2),
            "enable": base_mlm.get("enable", True),
        }

        # 添加 Consul 配置
        consul_config = raw_config.get("consul", {})
        consul_settings = ConsulSettings(**consul_config)

        # 添加 Service 配置
        service_config = raw_config.get("service", {})
        service_settings = ServiceSettings(**service_config)

        # 添加插件配置处理
        plugins_config = raw_config.get("plugins", {})
        plugins_settings = PluginSettings(
            fetcher=FetcherPluginSettings(**plugins_config.get("fetcher", {})),
            search=SearchPluginV2Settings(
                **plugins_config.get("search ", {})) if "search" in plugins_config else None,
            weather=WeatherPluginSettings(**plugins_config.get("weather", {})) if "weather" in plugins_config else None
        )

        # 添加 Selenium 配置
        selenium_config = raw_config.get("selenium", {})
        selenium_settings = SeleniumSettings(**selenium_config)

        # 添加 cent_svs 配置
        cent_svs_config = raw_config.get("cent_svs", {})
        cent_svs_settings = CentSvsSettings(**cent_svs_config)

        config_dict = {
            "llm": {
                "default": llm_default_settings,
                **{
                    name: {**llm_default_settings, **override_config}
                    for name, override_config in llm_overrides.items()
                },
            },
            "mlm": {
                "default": mlm_default_settings,
                **{
                    name: {**mlm_default_settings, **override_config}
                    for name, override_config in mlm_overrides.items()
                },
            },
            "consul": consul_settings,
            "service": service_settings,
            "plugins": plugins_settings,
            "selenium": selenium_settings,
            "cent_svs": cent_svs_settings  # 新增的配置项
        }

        self._config = AppConfig(**config_dict)

    @property
    def llm(self) -> Dict[str, LLMSettings]:
        if self._config is None:
            raise ValueError("Config not loaded")
        return self._config.llm

    @property
    def mlm(self) -> Dict[str, MLMSettings]:
        if self._config is None:
            raise ValueError("Config not loaded")
        return self._config.mlm

    @property
    def consul(self) -> ConsulSettings:
        if self._config is None:
            raise ValueError("Config not loaded")
        return self._config.consul

    @property
    def service(self) -> ServiceSettings:
        if self._config is None:
            raise ValueError("Config not loaded")
        return self._config.service

    @property
    def plugins(self) -> Optional[PluginSettings]:
        if self._config is None:
            raise ValueError("Config not loaded")
        return self._config.plugins

    @property
    def selenium(self) -> Optional[SeleniumSettings]:
        if self._config is None:
            raise ValueError("Config not loaded")
        return self._config.selenium

    @property
    def cent_svs(self) -> CentSvsSettings:
        if self._config is None:
            raise ValueError("Config not loaded")
        return self._config.cent_svs


# config = Config()

# def get_config() -> Config:
#     """
#     返回 Config 单例实例。主进程入口调用一次以完成初始化。
#     """
#     return Config()
