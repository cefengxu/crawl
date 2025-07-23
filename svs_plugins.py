import argparse
import asyncio
import os
import signal
import socket
# import uuid
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime

# import consul
import uvicorn
from art import text2art
from fastapi import FastAPI, HTTPException
from uvicorn.server import Server

# from modules.process.bing_process import SearchRequestModel, BingSearchProcess
# from modules.process.bing_v2_process import BingSearchV2Process
# from modules.process.search_process import SearchV2RequestModel, SearchProcess
from modules.plugins.fetcher.common.fetch_context import FetchContext
from modules.task_progress import TaskProgressManager
from modules.utils.config import Config
from modules.utils.koba_logger import KobaLogger
from modules.process.koba_example import ExampleModel,  ExampleProcess
# from modules.process.search_process_v2 import SearchV2Model, SearchProcessV2
# from modules.process.fetch_process import FetchModel, FetchProcess
from modules.process.fetch_process_business import FetchModelBusiness, FetchProcessBusiness
# from modules.process.weather_process import WeatherModel, WeatherProcess
# from modules.plugins.base_request_model import SearchModel
# from modules.process.search_process import SearchProcess
from modules.process.search_process_business import SearchProcessBusiness
from modules.plugins.base_request_model import SearchModelBusiness
from modules.process.crawl_process import CrawlProcess
# from modules.process.rerank_process import RerankerProcess
# from modules.plugins.base_request_model import RerankRequest
from modules.utils.verify import verify

_service_id: str = ""
_shutdown_in_progress: bool = False
_uvicorn_server: Optional[Server] = None  # 添加全局变量来存储uvicorn服务器实例

k: Optional[KobaLogger] = None
c: Optional[Config] = None
t: Optional[TaskProgressManager] = None


def get_local_ip() -> str:
    # global config
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.connect((config["consul"]["host"], config["consul"]["port"]))
        s.connect((Config.app_config.consul.host, Config.app_config.consul.port))
        local_ip = s.getsockname()[0]
        s.close()
        # print("[*]", local_ip)
        return local_ip
    except Exception as e:
        print(f"获取本地IP时出错: {e}")
        return "127.0.0.1"


# def register_to_consul() -> None:
#     # global config, _service_id
#     global _service_id
#     # c = consul.Consul(host=config["consul"]["host"], port=config["consul"]["port"])
#     c = consul.Consul(host=Config.app_config.consul.host, port=Config.app_config.consul.port)
#     _local_ip = get_local_ip()
#     _service_id = str(uuid.uuid4())
#     c.agent.service.register(
#         name="ainT.Plugins",
#         service_id=_service_id,
#         address=_local_ip,
#         # port=config["service"]["port"],
#         # check=consul.Check.http(
#         #     f'http://{get_local_ip()}:{config["service"]["port"]}/api/v1/plgi/{_service_id}/health',
#         #     interval=config["consul"]["interval"],
#         # ),
#         port=Config.app_config.service.port,
#         check=consul.Check.http(
#             f'http://{get_local_ip()}:{Config.app_config.service.port}/api/v1/plgi/{_service_id}/health',
#             interval=Config.app_config.consul.interval,
#         ),
#     )


# def deregister_from_consul(service_id) -> None:
#     # global config
#     # c = consul.Consul(host=config["consul"]["host"], port=config["consul"]["port"])
#     c = consul.Consul(host=Config.app_config.consul.host, port=Config.app_config.consul.port)
#     c.agent.service.deregister(service_id)


def handle_signal(signum, frame):
    global _shutdown_in_progress
    if _shutdown_in_progress:
        print("Shutdown already in progress. Please wait...")
        return

    _shutdown_in_progress = True
    print("Received signal to shutdown. Shutting down...")
    # 不再直接调用os._exit(0)，而是等待FastAPI完成清理
    asyncio.get_event_loop().stop()
    # SeleniumManage.clear_all_driver()
    # deregister_from_consul(_service_id)
    # os._exit(0)


@asynccontextmanager
async def lifespan(app):
    global _service_id
    # 启动时初始化Dask客户端
    TaskProgressManager.task_manager._ensure_client()
    KobaLogger.logger_koba.info("Dask客户端已初始化")
    # 启动时的逻辑（如果需要）

    yield

    # 关闭时清理资源
    if TaskProgressManager.task_manager._dask_client is not None:
        KobaLogger.logger_koba.info("正在关闭Dask客户端...")
        TaskProgressManager.task_manager._dask_client.close()
        TaskProgressManager.task_manager._dask_client = None

    # 关闭时的逻辑（之前在shutdown_event中的代码）
    print("FastAPI shutdown event triggered. Cleaning up resources...")
    # SeleniumManage.clear_all_driver()

    print("Shutdown complete.")


# 使用lifespan参数创建FastAPI应用
app = FastAPI(lifespan=lifespan)


@app.get("/api/v1/plgi/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }



@app.post("/api/v1/plgi/example")
async def example(item: ExampleModel):
    try:
        KobaLogger.logger_koba.info(f"[*/api/v1/plgi/example] {item}")

        example_service = ExampleProcess(item)
        TaskProgressManager.task_manager.register_task(item.task_id, example_service)

        result = await TaskProgressManager.task_manager.process_task(item.task_id)

        response = {"status": 200, "msg": "success.", "data": result}
        # logger_koba.info(f"[*] {response}")
        return response

    except Exception as e:
        KobaLogger.logger_koba.error(f"[*] {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        TaskProgressManager.task_manager.remove_task(item.task_id)  # 删除任务




@app.post("/api/v1/plgi/search")
async def create_search(item: SearchModelBusiness):
    try:
        KobaLogger.logger_koba.info(f"[*/api/v1/plgi/search] {item}")
        
        if not verify(item.key, "search"):
            # raise Exception("verify fail")
            return {"status": 401, "msg": "verify fail", "data": {}}    

        search_service = SearchProcessBusiness(item)
        TaskProgressManager.task_manager.register_task(item.task_id, search_service)

        result = await TaskProgressManager.task_manager.process_task(item.task_id)

        response = {"status": 200, "msg": "success.", "data": result}
        return response

    except Exception as e:
        KobaLogger.logger_koba.error(f"[*] {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        TaskProgressManager.task_manager.remove_task(item.task_id)  # 删除任务


@app.post("/api/v1/plgi/crawl")
async def create_crawl(item: FetchModelBusiness):
    try:
        KobaLogger.logger_koba.info(f"[*/api/v1/plgi/crawl] {item}")
        
        if not verify(item.key, "fetch"):
            # raise Exception("verify fail")
            return {"status": 401, "msg": "verify fail", "data": {}}    


        fetch_service = FetchProcessBusiness(item)
        TaskProgressManager.task_manager.register_task(item.task_id, fetch_service)

        result = await TaskProgressManager.task_manager.process_task(item.task_id)

        context: FetchContext = result["results"]
        result["results"]={
            'status':context.status,
            'pipeline':context.pipeline,
            'response':{
                'length':context.response.md_length if context.response else 0,
                'md':context.response.final_md if context.response else "",
                
            }
        }
        status = 200
        msg = "success"

        if context.status and context.status.status == "verify fail":
            status = 401
            msg = "verify fail"
        response = {"status": status, "msg": msg, "data": result}
        # logger_koba.info(f"[*] {response}")
        return response

    except Exception as e:
        KobaLogger.logger_koba.error(f"[*] {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        TaskProgressManager.task_manager.remove_task(item.task_id)  # 删除任务

@app.post("/api/v1/plgi/search-crawl")
async def create_search_crawl(item: SearchModelBusiness):
    try:
        KobaLogger.logger_koba.info(f"[*/api/v1/plgi/search-crawl] {item}")
        
        if item.rerank_engine == True:
            if not verify(item.key, "crawl+rerank"):
                # raise Exception("verify fail")
                return {"status": 401, "msg": "verify fail", "data": {}}
        else:
            if not verify(item.key, "crawl"):
                return {"status": 401, "msg": "verify fail", "data": {}}      
        
          

        crawl_service = CrawlProcess(item)
        TaskProgressManager.task_manager.register_task(item.task_id, crawl_service)

        result = await TaskProgressManager.task_manager.process_task(item.task_id)

        response = {"status": 200, "msg": "success.", "data": result}
        return response

    except Exception as e:
        KobaLogger.logger_koba.error(f"[*] {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        TaskProgressManager.task_manager.remove_task(item.task_id)  # 删除任务


# @app.post("/api/v1/plgi/rerank")
# async def create_rerank(item: RerankRequest):
#     try:
#         KobaLogger.logger_koba.info(f"[*/api/v1/plgi/rerank]")
        
#         rerank_service = RerankerProcess(item)
#         TaskProgressManager.task_manager.register_task(item.task_id, rerank_service)

#         result = await TaskProgressManager.task_manager.process_task(item.task_id)

#         response = {"status": 200, "msg": "success.", "data": result}
#         return response
#     except Exception as e:      
#         KobaLogger.logger_koba.error(f"[*] {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         TaskProgressManager.task_manager.remove_task(item.task_id)  # 删除任务  

# async def _process_weather_request(item: WeatherModel, endpoint_type: str):
#     try:
#         KobaLogger.logger_koba.info(f"[*/api/v2/plgi/{endpoint_type}] {item}")

#         weather_service = WeatherProcess(item)
#         TaskProgressManager.task_manager.register_task(item.task_id, weather_service)

#         result = await TaskProgressManager.task_manager.process_task(item.task_id)

#         response = {"status": 200, "msg": "success.", "data": result}
#         return response
    
#     except Exception as e:
#         KobaLogger.logger_koba.error(f"[*] {e}")
#         raise HTTPException(status_code=500, detail=str(e))

#     finally:
#         TaskProgressManager.task_manager.remove_task(item.task_id)  # 删除任务

# @app.post("/api/v2/plgi/weather")
# async def create_weather(item: WeatherModel):
#     return await _process_weather_request(item, "weather")

# @app.post("/api/v2/plgi/forecast")
# async def create_forecast(item: WeatherModel):
#     return await _process_weather_request(item, "forecast")

def main(port: Optional[int] = None):
    global app, _uvicorn_server, k, c, t   # , search_service, search_service_v2, weather_service, fetch_service  # ，crawl_service
    
    k = KobaLogger()
    c = Config()
    t = TaskProgressManager()

    if port is not None:
        # config["service"]["port"] = port
        Config.app_config.service.port = port

    signal.signal(signal.SIGINT, handle_signal)

    try:
        # # 初始化插件
        # searcher_1, weather_1 = init_plugins(config)
        # searcher_1, weather_1 = init_plugins()
        # bocha_search = BochaSearch()
        # exa_search = EXASearch()
        # # 设置searcher
        # # 设置searcher
        # search_service.set_searcher(searcher_1)
        # bocha_search_service.set_searcher(bocha_search)
        # exa_search_service.set_searcher(exa_search)
        # weather_service.set_weather(weather_1)
        KobaLogger.logger_koba.info(f'\n{text2art("ainT.Plugins")}')
        KobaLogger.logger_koba.info(f"Version: 0.7.10.9")

        """
        0.x.1.x : bing search
        0.x.2.x : weather
        0.x.3.x : crawl = sync crawl via jina / firecrawl
        0.x.4.x : 靓汤
        0.x.5.x : selenium框架
        0.6.x.x : 优化代码，更新获取当地时间函数
        0.7.x.x : selenium植入
        """


        # 使用Server类而不是run函数，这样可以控制服务器的关闭
        config = uvicorn.Config(app, host="0.0.0.0", port=Config.app_config.service.port,
                                reload=False, timeout_keep_alive=3)
        _uvicorn_server = uvicorn.Server(config)
        # 运行服务器
        asyncio.run(_uvicorn_server.serve())
        # uvicorn.run(app, host="0.0.0.0", port=app_config.service.port, reload=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        KobaLogger.logger_koba.error(f"An error occurred: {str(e)}")
    finally:
        pass


if __name__ == "__main__":
    k = KobaLogger()
    c = Config()
    t = TaskProgressManager()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str,
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml"))
    args = parser.parse_args()

    # 从配置文件加载默认值
    # load_config(args.config)
    KobaLogger.logger_koba.info("测试日志输出")
    main()
