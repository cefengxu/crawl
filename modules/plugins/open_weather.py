import requests
from typing import Optional
from pydantic import BaseModel, Field
import json

from datetime import datetime, timedelta
from modules.utils.config import Config
# from .base_searcher import BaseSearcher
from .base_request_model import WeatherModel
from .base_plugin import BasePlugin
# VERSION = '0.1.0'


# def register_weather(encoder_args_dict={}):
#     # if encoder_args_dict["model_name"] not in encoder_name_map_dict.keys():
#         # raise "Can't Find Encoder Model: {}".format(encoder_args_dict["model_name"])

#     # model_name = encoder_name_map_dict[encoder_args_dict["model_name"]]

#     return globals()['OpenWeather'](encoder_args_dict)

class OpenWeather(BasePlugin):
    def __init__(self, item: WeatherModel):
        super().__init__(item)
        # self.api_key = encoder_args_dict['subscription_key']
        # self.url_weather = encoder_args_dict['endpoint_weather']
        # self.url_forecast = encoder_args_dict['endpoint_forecast']
        # self.VERSION = VERSION
        
        self.api_key = Config.app_config.plugins.weather.subscription_key
        self.url_weather = Config.app_config.plugins.weather.endpoint_weather
        self.url_forecast = Config.app_config.plugins.weather.endpoint_forecast
        self.VERSION = '0.1.0'
        
        # 判断 num_days 是否是用户输入的
        self.is_num_days_provided = 'num_days' in item.model_fields_set
        print(f"天数是否用户指定: {self.is_num_days_provided}, 天数为: {item.num_days}天")
        
        
    # def search(self, location: str, format: str = "metric", num_days: int = 1):
    def search(self, **kwargs):
        params = {
            "q": kwargs.get('location',''), 
            "appid": self.api_key,
            "units": kwargs.get('format','metric')
        }
        
        try:
            response = requests.get(self.url_weather, params=params)
            response.raise_for_status()
            
            data = response.json()
            # print('[response]',data)
            result = {
                "城市": data['name'],
                "温度": data["main"]["temp"],
                "湿度": data["main"]["humidity"],
                "描述": data["weather"][0]["description"],
                "version": self.VERSION
            }
            return result
        except Exception as ex:
            raise ex

    # def get_current_weather(self,location, format="celsius", num_days=1):
    def get_current_weather(self, **kwargs):
        """获取指定位置的当前天气"""
        
        params = {
            "q": kwargs.get('location',''),
            "appid": self.api_key,
            #"units": "metric" if format == "celsius" else "imperial",
            "units": kwargs.get('format','metric')
        }

        try:
            response = requests.get(self.url_weather, params=params)
            response.raise_for_status()
            data = response.json()

            weather_info = [{
                "date": datetime.now().strftime("%Y-%m-%d"),
                "weather": data['weather'][0]['description'],
                "temp_min": round(data['main']['temp_min'], 1),
                "temp_max": round(data['main']['temp_max'], 1),
                "humidity": round(data['main']['humidity'], 1),
                "unit": "°C" if format == "celsius" else "°F"
            }]

       
            return weather_info
        except requests.RequestException as e:
          
            return {"error": str(e)}
        
    # def get_n_day_weather_forecast(self,location, format="celsius", num_days=3):
    def get_n_day_weather_forecast(self, **kwargs):
        """获取指定位置未来n天的天气预报"""
        #api_url = "http://api.openweathermap.org/data/2.5/forecast"
        #api_key = "e42cd297db7adabc43a0f1e35115dd51"  # 请替换为您的实际API密钥
        print('[***kwargs***]',kwargs)
        num_days = kwargs.get('num_days',3)
        params = {
            "q": kwargs.get('location',''),
            "appid": self.api_key,
            "units": kwargs.get('format','metric'),
            "cnt": 8 * num_days,  # 每天8个3小时间隔的数据点
        }

        try:
            response = requests.get(self.url_forecast, params=params)
            response.raise_for_status()
            data = response.json()
            # print('[*data*]',json.dumps(data,ensure_ascii=False))
            current_date = datetime.now().date()
            forecast = []

            for item in data['list']:
                date = datetime.fromtimestamp(item['dt']).date()
                
                if date > current_date and (date - current_date).days <= num_days:
                    if not forecast or forecast[-1]['date'] != date.strftime("%Y-%m-%d"):
                        forecast.append({
                            "date": date.strftime("%Y-%m-%d"),
                            "weather": [],
                            "temp_min": float('inf'),
                            "temp_max": float('-inf'),
                            "humidity": []
                        })
                    
                    day_forecast = forecast[-1]
                    day_forecast['weather'].append(item['weather'][0]['description'])
                    day_forecast['temp_min'] = min(day_forecast['temp_min'], item['main']['temp_min'])
                    day_forecast['temp_max'] = max(day_forecast['temp_max'], item['main']['temp_max'])
                    day_forecast['humidity'].append(item['main']['humidity'])

            for day in forecast:
                day['weather'] = max(set(day['weather']), key=day['weather'].count)
                day['humidity'] = round(sum(day['humidity']) / len(day['humidity']), 1)
                day['temp_min'] = round(day['temp_min'], 1)
                day['temp_max'] = round(day['temp_max'], 1)
                day['unit'] = "°C" if format == "celsius" else "°F"

            # return json.dumps(forecast, ensure_ascii=False)
            return forecast
        except requests.RequestException as e:
            # return json.dumps({"error": str(e)})
            return {"error": str(e)}


    async def process(self):
        if self.is_num_days_provided:
            return self.get_n_day_weather_forecast(
                location=self.item.location,
                format=self.item.format,
                num_days=self.item.num_days
            )
        if not self.is_num_days_provided:
            return self.get_current_weather(
                location=self.item.location,
                format=self.item.format,
                num_days=self.item.num_days
            )
# 使用示例
# if __name__ == "__main__":
    
#     encoder_args_dict ={
#         'enabled': True, 
#         'subscription_key': 'e42cd297db7adabc43a0f1e35115dd51', 
#         'endpoint_weather': 'http://api.openweathermap.org/data/2.5/weather', 
#         'endpoint_forecast': 'http://api.openweathermap.org/data/2.5/forecast'
#         }
    
#     weather_searcher = register_weather(encoder_args_dict)
#     weather_info = weather_searcher.search(location="beijing")
#     print(f"北京的天气: 温度 {weather_info['温度']}°C, 湿度 {weather_info['湿度']}%, {weather_info['描述']}")
