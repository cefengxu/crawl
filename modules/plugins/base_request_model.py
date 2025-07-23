from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class ParamsModel(BaseModel):
    mkt: Optional[str] = Field(default="zh-CN")
    category: Optional[str] = Field(default="")
    freshness: Optional[str] = Field(default="")
    invoke: Optional[str] = Field(default='rest')
    crawler: Optional[bool] = Field(default=False)

class SearchModelBusiness(BaseModel):
    query: str
    count: int
    params: Optional[ParamsModel] = None
    search_engine: Optional[str] = Field(default="baidu")
    fetch_engine: Optional[str] = Field(default="none")
    task_id: Optional[str] = None
    key: str = Field(default="")
    rerank_engine: Optional[bool]  = Field(default=False)

    def __init__(self, **data):
        if 'task_id' not in data or data['task_id'] is None:
            data['task_id'] = str(uuid.uuid4())
        if 'params' in data and isinstance(data['params'], dict):
            data['params'] = ParamsModel(**data['params'])
        super().__init__(**data)

class SearchModel(BaseModel):
    query: str
    count: int
    params: Optional[ParamsModel] = None
    search_engine: Optional[str] = Field(default="tavily")
    fetch_engine: Optional[str] = Field(default="none")
    task_id: Optional[str] = None
    

    def __init__(self, **data):
        if 'task_id' not in data or data['task_id'] is None:
            data['task_id'] = str(uuid.uuid4())
        if 'params' in data and isinstance(data['params'], dict):
            data['params'] = ParamsModel(**data['params'])
        super().__init__(**data)

class WeatherModel(BaseModel):
    location: str
    format: Optional[str] = Field(default="metric")  # metric / imperial / standard
    num_days: Optional[int] = Field(default=3)
    task_id: Optional[str] = None

    def __init__(self, **data):
        if 'task_id' not in data or data['task_id'] is None:
            data['task_id'] = str(uuid.uuid4())
        super().__init__(**data)

class FetchParamsModel(BaseModel):
    context_cache: Optional[bool] = Field(default=False) # markdown file and context cache save
    browser_only: Optional[bool] = Field(default=False)
    reranker: Optional[bool] = Field(default=False)

class FetchModel(BaseModel):
    url: str
    fetch_engine: Optional[str] = Field(default="selenium")  # selenium, selenium_only, http, cl_chrome, cl_camoufox
    parser: Optional[str] = Field(default="normal")  # md5, sum, sum_v2, html
    info: Optional[bool] = Field(default=False)  # True / False
    task_id: Optional[str] = None
    params:Optional[FetchParamsModel] = Field(default=FetchParamsModel())
    key: Optional[str] = Field(default="")

    def __init__(self, **data):
        if 'task_id' not in data or data['task_id'] is None:
            data['task_id'] = str(uuid.uuid4())
        super().__init__(**data)

class FetchModelBusiness(BaseModel):
    url: str
    fetch_engine: Optional[str] = Field(default="selenium")  # selenium, selenium_only, http, cl_chrome, cl_camoufox
    parser: Optional[str] = Field(default="normal")  # md5, sum, sum_v2, html
    info: Optional[bool] = Field(default=False)  # True / False
    task_id: Optional[str] = None
    params:Optional[FetchParamsModel] = Field(default=FetchParamsModel())
    key: str = Field(default="")

    def __init__(self, **data):
        if 'task_id' not in data or data['task_id'] is None:
            data['task_id'] = str(uuid.uuid4())
        super().__init__(**data)

class RerankRequest(BaseModel):
    model: str = "Qwen3-Reranker-0.6B"
    instruction: Optional[str] = Field(default="Given the user query, retrieval the relevant passages")
    text_1: List[str]
    text_2: List[str]
    task_id: Optional[str] = None

    def __init__(self, **data):
        if 'task_id' not in data or data['task_id'] is None:
            data['task_id'] = str(uuid.uuid4())
        super().__init__(**data)