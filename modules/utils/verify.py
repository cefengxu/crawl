import requests
from .koba_logger import KobaLogger
from ..utils.config import Config

def verify(key,service_type = "search"):
    url = f"http://{Config.app_config.cent_svs.host}:{Config.app_config.cent_svs.port}/api/v1/api-keys/verify/{key}?app_id=app-c"
    data = {
   
        "service_type": service_type
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            response_data = response.json()
            #print(response_data)
            if response_data.get("is_valid") == True:
                return True
            return False
        else:
            raise Exception(f"request fail: {response.status_code} ")
    except Exception as e:
        KobaLogger.logger_koba.error(f"verify fail : {e}")
        return False