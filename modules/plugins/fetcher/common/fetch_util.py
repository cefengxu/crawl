from datetime import datetime
from enum import Enum
import json
from pathlib import Path
from urllib.parse import urlparse

# import crawlee
from html2text import html2text
from modules.plugins.fetcher.common.fetch_context import FetchContext
from modules.utils.koba_logger import KobaLogger
import os
import re
import time
import aiofiles
from bs4 import BeautifulSoup
import requests
from readability import Document
from markdownify import markdownify as md
from trafilatura import extract,extract_metadata,html2txt
#from crawlee.crawlers import RenderingTypePredictor
#from crawlee.crawlers._adaptive_playwright._rendering_type_predictor import DefaultRenderingTypePredictor

from .s_logging import fetch_logger


# def is_dynamic(url):
#     predictor = DefaultRenderingTypePredictor()
#     request = crawlee.Request.from_url(url)
#     prediction = predictor.predict(request)
#     if prediction.rendering_type == "static":
#         return False
#     return True 

def sum_html_readabilipy(html:str):
    doc = Document(html)
    content = doc.summary()  # 获取主要内容
    title = doc.short_title()[:20]
    return content,title

def sum_html_trafilatura(html:str):
    content = extract(html, output_format="markdown",no_fallback=True)
    return content

def sum_html(html:str):
    doc = Document(html)
    content = doc.summary()  # 获取主要内容
    return content

def get_title(html:str):
    meta = extract_metadata(html)
    if meta.title:
        return meta.title[:20]
    elif meta.description:
        return meta.description[:20]
    else:
        return "None"

def get_title_readability(html:str):
    doc = Document(html)
    return doc.short_title()[:20]

def get_text_BS(html:str,strip=False):
    soup = BeautifulSoup(html, 'html.parser')
    # 提取所有文本
    text = soup.get_text(strip=strip)
    return text

def get_text_v2(html:str):
    res = html2txt(html)
    return res

def get_text_v1(html:str):
    md = html2text(html)
    res = clean_md(md).strip()
    res=remove_duplicate_lines(res)
    return res

def get_md(html:str):
    md = html2text(html)
    res = clean_md(md).strip()
    return res

def sum_md(md:str):
    res=remove_duplicate_lines(md)
    return res

def remove_duplicate_lines(input_string):
    # 按行分割字符串
    lines = input_string.split('\n')
    # 使用集合去重并保持顺序
    seen = set()
    unique_lines = []
    
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)
    
    # 将去重后的行合并回字符串
    return ''.join(unique_lines)

def get_bs_md(html:str,strip=False):
    soup = BeautifulSoup(html, 'html.parser')
    # 提取所有文本
    text = soup.get_text(strip=strip)
    return md(text)

class RerankModel(Enum):
    JINA = "jina-reranker-v2-base-multilingual"
    BGE = "bge-reranker-v2-m3"
    



# Patterns
SCRIPT_PATTERN = r"<[ ]*script.*?\/[ ]*script[ ]*>"
STYLE_PATTERN = r"<[ ]*style.*?\/[ ]*style[ ]*>"
META_PATTERN = r"<[ ]*meta.*?>"
COMMENT_PATTERN = r"<[ ]*!--.*?--[ ]*>"
LINK_PATTERN = r"<[ ]*link.*?>"
BASE64_IMG_PATTERN = r'<img[^>]+src="data:image/[^;]+;base64,[^"]+"[^>]*>'
SVG_PATTERN = r"(<svg[^>]*>)(.*?)(<\/svg>)"
ANCHOR_PATTERN = r"<[ ]*a [^>]*>.*?<[ ]*\/[ ]*a[ ]*>"
ANCHOR_PATTERN2 = r"<a[^>]*>(.*?)<\/a>"

SCRIPT_REGEX = re.compile(SCRIPT_PATTERN, flags=re.IGNORECASE | re.DOTALL)
STYLE_REGEX = re.compile(STYLE_PATTERN, flags=re.IGNORECASE | re.DOTALL)
COMMENT_REGEX = re.compile(COMMENT_PATTERN, flags=re.IGNORECASE | re.DOTALL)
LINK_REGEX = re.compile(LINK_PATTERN, flags=re.IGNORECASE | re.DOTALL)

def clean_html_V2(html: str, clean_svg: bool = True, clean_base64: bool = True):
    html = SCRIPT_REGEX.sub("", html)
    html = STYLE_REGEX.sub("", html)
    html = COMMENT_REGEX.sub("", html)
    html = LINK_REGEX.sub("", html)

    if clean_svg:
        html = replace_svg(html)
    if clean_base64:
        html = replace_base64_images(html)

    #html=replace_meta(html)

    return html


def clean_html(html: str, clean_svg: bool = True, clean_base64: bool = True):
    html = re.sub(
        SCRIPT_PATTERN, "", html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    html = re.sub(
        STYLE_PATTERN, "", html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    # html = re.sub(
    #     META_PATTERN, "", html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL
    # )
    html = re.sub(
        COMMENT_PATTERN, "", html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    html = re.sub(
        LINK_PATTERN, "", html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    # html = re.sub(
    #     ANCHOR_PATTERN, "", html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL
    # )

    # html = re.sub(
    #     ANCHOR_PATTERN2, '', html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL
    # )

    if clean_svg:
        html = replace_svg(html)
    if clean_base64:
        html = replace_base64_images(html)

    html=replace_meta(html)

    return html

def get_token(str):
    try:
        url="http://10.176.14.23:9402/api/v1/models/tokenizer"
        payload = {
            "content": str,
            "model": "tokenizer-qwen"
        }
        response = requests.post(url, json=payload)

        # 检查响应状态码
        if response.status_code == 200:
            # 请求成功，打印响应内容
            response_data = response.json()
            data = response_data.get("data", {})
            len = data.get("len", 0)
            return len
        else:
            raise Exception(f"get_token failed with status code:{response.status_code}")
    except Exception as e:
        raise Exception(f"get_token fail: {e}")
    
def replace_base64_images(html: str, new_image_src: str = "#") -> str:
    return re.sub(BASE64_IMG_PATTERN, f'<img src="{new_image_src}"/>', html)

def replace_svg(html: str, new_content: str = "") -> str:
    return re.sub(
        SVG_PATTERN,
        lambda match: f"{match.group(1)}{new_content}{match.group(3)}",
        html,
        flags=re.DOTALL,
    )

def replace_meta(html):
    soup = BeautifulSoup(html, 'html.parser')
    # 1. 找到目标 meta 标签
    title_metas = soup.find_all('meta', {'property':'og:title'})
    des_metas = soup.find_all('meta', {'property': 'og:description'})

    if len(title_metas) > 0:
        for meta_tag in title_metas:
            # 2. 提取 content 属性的值
            content = meta_tag.get('content', '')
            
            # 3. 创建新的 <p> 标签，并将 content 的值作为文本插入
            new_p_tag = soup.new_tag('p')
            new_p_tag.string = f'"{content}"'  # 添加双引号（根据需求可选）
            
            # 4. 用新 <p> 标签替换原 <meta> 标签
            meta_tag.replace_with(new_p_tag)  
    
    if len(des_metas) > 0:
        for meta_tag in des_metas:
            # 2. 提取 content 属性的值
            content = meta_tag.get('content', '')
            
            # 3. 创建新的 <p> 标签，并将 content 的值作为文本插入
            new_p_tag = soup.new_tag('p')
            new_p_tag.string = f'"{content}"'  # 添加双引号（根据需求可选）
            
            # 4. 用新 <p> 标签替换原 <meta> 标签
            meta_tag.replace_with(new_p_tag) 

    return soup.prettify()

async def save_md_async(md, filename):
    try:
        directory = os.path.dirname(filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        async with aiofiles.open(filename, "w", encoding="utf-8") as f:
            await f.write(md)
    except Exception as e:
        fetch_logger.error("save md %s fail: %s", filename, e)

def save_md(md, filename):
    try:
        directory = os.path.dirname(filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(md)
            fetch_logger.info("save md %s success", filename)
    except Exception as e:
        fetch_logger.error("save md %s fail: %s", filename, e)

def save_html(html, filename):
    try:
        directory = os.path.dirname(filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
            fetch_logger.info("save html %s success", filename)
    except Exception as e:
        fetch_logger.error("save html %s fail: %s", filename, e)

def save_file(context, filename):
    try:
        directory = os.path.dirname(filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(context)
            fetch_logger.info("save file %s success", filename)
    except Exception as e:
        fetch_logger.error("save file %s fail: %s", filename, e)


DEFAULT_CACHE_DIR = os.path.join(Path(__file__).resolve().parent.parent.parent.parent.parent,"cache")
DEFAULT_CACHE_FETCH_DIR = os.path.join(DEFAULT_CACHE_DIR,"fetch")
DEFAULT_CACHE_CONTEXT_DIR = os.path.join(DEFAULT_CACHE_FETCH_DIR, "context")
def save_context(context:FetchContext, filepath=DEFAULT_CACHE_CONTEXT_DIR):
    try:
        current_time = datetime.now().strftime("%Y%m%d")  # 格式：年月日_时分秒
        filename = f"context_ouput_{current_time}.json"
        full_path = os.path.join(filepath, filename)
        if filepath:
            os.makedirs(filepath, exist_ok=True)
        with open(full_path, "a") as f:
            json.dump(context.model_dump(exclude="response"), f, indent=2)
        fetch_logger.info(f"{context.taskid} context output")
    except Exception as e:
        fetch_logger.error(f"{context.taskid} context output fail: {e}")


CM_PATTERN = r'\[(.*?)\]\(.*?\)'
CM_REGEX = re.compile(CM_PATTERN, flags=re.IGNORECASE | re.DOTALL)
def clean_md(md):
   while True:
        new_md, substitution_count = CM_REGEX.subn(r'\1', md)
        if substitution_count == 0:
            break
        md = new_md
   return md

def clean_markdown(md_str):
    # 统一换行符为\n
    md_str = md_str.replace('\r\n', '\n').replace('\r', '\n')
    lines = md_str.split('\n')
    processed_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        if line_stripped:
            # 检查是否包含字母、数字、汉字
            if re.search(r'[a-zA-Z0-9\u4e00-\u9fff]', line_stripped):
                processed_lines.append(line)
            # 否则，不保留该行
        else:
            # 将全为空白字符的行视为空行
            processed_lines.append('')
    
    # 合并处理后的行并清理连续的换行符
    processed_content = '\n'.join(processed_lines)
    processed_content = re.sub(r'\n{3,}', '\n\n', processed_content)
    
    return processed_content.strip('\n')

def is_valid_url(url):
    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return False
        path = parsed_url.path
        _, ext = os.path.splitext(path)
        err_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.exe', '.dmg', '.iso', '.img', '.apk', '.ipa', '.deb', '.rpm', '.msi', '.jar', '.war', '.ear', '.apk', '.ipa', '.deb', '.rpm', '.msi', '.jar', '.war', '.ear']
        if ext.lower() in err_extensions:
            return False
        
        if ".pdf" in url:
            return False
        return True
    except ValueError:
        return False
    

def is_dynamic_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    _, ext = os.path.splitext(path)
    dynamic_extensions = ['.shtml', '.jsp', '.asp', '.aspx', '.do', 
                          '.action', '.jspx', '.jspf', '.jhtm', '.jhtml']
    if ext.lower() in dynamic_extensions:
        return True

    return False

def is_dynamic_rendered(url,html):
    s1 = time.time()

    """通过静态HTML特征判断动态渲染可能性"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # 特征检测字典
    clues = {
        'framework_tags': False,
        'async_scripts': False,
        'spa_patterns': False,
        'empty_content': False,
        'hydration_markers': False,
        'data_attributes': False
    }

    # 1. 检测前端框架特征
    framework_patterns = {
        'react': [r'__reactContainer', r'data-reactroot'],
        'vue': [r'v-[\w-]+=', r'data-v-[\w-]+'],
        'angular': [r'ng-[\w-]+=', r'_nghost_'],
        'svelte': [r'class="svelte-[\w]+"'],
        'nextjs': [r'__NEXT_DATA__']
    }
    
    for framework, patterns in framework_patterns.items():
        for pattern in patterns:
            if re.search(pattern, html, re.IGNORECASE):
                clues['framework_tags'] = True
                break

    # 2. 检测异步脚本
    scripts = soup.find_all('script')
    for script in scripts:
        src = script.get('src', '').lower()
        if any(keyword in src for keyword in ['react', 'vue', 'angular', 'chunk', 'bundle']):
            clues['async_scripts'] = True
        if script.get('type') in ['module', 'text/babel']:
            clues['async_scripts'] = True

    # 3. 单页应用(SPA)特征
    if soup.find('app-root') or soup.find('div', id='root'):
        clues['spa_patterns'] = True

    # 4. 主要内容区域空检测
    main_content = soup.find(['main', 'article']) or soup.find(class_=re.compile(r'content|main'))
    if main_content and len(main_content.text.strip()) < 100:
        clues['empty_content'] = True

    # 5. 检测hydration标记（SSR但需要客户端hydration）
    if re.search(r'hydration|hydrate', html, re.IGNORECASE):
        clues['hydration_markers'] = True

    # 6. 检测现代框架数据属性
    data_attrs = soup.find_all(attrs={re.compile(r'data-[\w-]+'): True})
    unique_attrs = len({k for tag in data_attrs for k in tag.attrs if k.startswith('data-')})
    if unique_attrs > 3:  # 现代框架通常使用多个数据属性
        clues['data_attributes'] = True

    # 综合判断逻辑
    dynamic_score = sum(clues.values())

    # 打印 clues 各项内容和总分
    log_message = f"{url} Dynamic complete: {dynamic_score}, cost: {time.time() - s1}s, clues: {clues}"
    fetch_logger.info(log_message)
    
    # 阈值判断（可根据需求调整）
    if dynamic_score >= 3:
        return True, clues
    else:
        return False, clues
    

def check_html(url,html):
    if "403 Forbidden" in html:
        fetch_logger.error(f"{url} html is 403 Forbidden")
        return False
    elif "Verifying you are human" in html:
        fetch_logger.error(f"{url} html is Verifying you are human")
        return False
    return True

