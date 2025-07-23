from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field



class FetchResponceContext(BaseModel):
    title:Optional[str] = Field(default='')
    http_html:Optional[str] = Field(default='NA')
    browser_html:Optional[str] = Field(default='NA')
    html:Optional[str] = Field(default='NA')
    md:Optional[str] = Field(default='NA')
    sum_md_tr:Optional[str] = Field(default='NA')
    sum_md_re:Optional[str] = Field(default='NA')
    final_md:Optional[str] = Field(default='NA')
    md_length:Optional[int] = Field(default=0)

class FetchPineLineContext(BaseModel):
    complete_time:Optional[float] = Field(default=0.0)
    http_time:Optional[float] = Field(default=0.0)
    broswer_time:Optional[float] = Field(default=0.0)
    parser_time:Optional[float] = Field(default=0.0)

class FetchOptionContext(BaseModel):
    fetch_type: str
    parse_type: str
    save_md: Optional[bool] = Field(default=False)

class FetchStatusContext(BaseModel):
    status:Optional[str] = Field(default='success')
    msg:Optional[str] = Field(default='')
    final_use_fetcher:Optional[str] = Field(default='NA')
    http_err:Optional[str] = Field(default=None)


class FetchContext(BaseModel):
    url: str
    taskid: str
    status:Optional[FetchStatusContext] = Field(default=FetchStatusContext())
    option:FetchOptionContext
    response: Optional[FetchResponceContext] = Field(default=FetchResponceContext())
    pipeline: Optional[FetchPineLineContext] = Field(default=FetchPineLineContext())

