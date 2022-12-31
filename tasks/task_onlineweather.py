import logging
from datetime import datetime
from os import path

from tasks.task_base import BaseTask
from tasks.config import WEATHER_API_ADDRESS, WEATHER_API_ZIPCODE, WEATHER_API_KEY, WEATHER_API_LAT, WEATHER_API_LONG
from tasks.helper import IssueHttpRequest, IssueSqlRequest

TEMP_GRAPH_PATH = path.join("generated_files", "temperatures.html")
TEMP_GRAPH_LONG_PATH = path.join("generated_files", "temperatures_long.html")
C02_GRAPH_PATH = path.join("generated_files", "co2.html")

class OutsideTempTask(BaseTask):
    """
    Task that fetches weather data from OpenWeather
    """
    def _add_init(self):
        pass
        
    def _intern_funct(self):
        res = self._get_temp()
        if (res is None):
            self.last_result = "Outside Temp: Not available"
            logging.error(self.last_result)
        else:
            self._save_temp(res)
            self.last_result = f"Outside Temp: {res:.1f}"
            logging.info(self.last_result)
            

    def _get_temp(self):
        call = ""
        if (WEATHER_API_ZIPCODE == ""):
            call = (WEATHER_API_ADDRESS + "/data/2.5/weather?lat=" +
                WEATHER_API_LAT + "&lon=" + WEATHER_API_LONG + "&APPID=" + WEATHER_API_KEY)
        else:
            call = (WEATHER_API_ADDRESS + "/data/2.5/weather?zip=" +
                WEATHER_API_ZIPCODE + ",ca&APPID=" + WEATHER_API_KEY)
        result = IssueHttpRequest(call)
        
        if result is None:
            return None
        else:
            return self._ConvertKelvinToCelcius(result.json()['main']['temp'])
        
    def _save_temp(self, temp):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        request = (f"INSERT INTO `environment` (`uid`, `datetime`, `value`, `type`, `description`, `unit`) "
            f"VALUES (NULL, '{now}','{temp}','2','OutsideTemp','degC')")
        IssueSqlRequest(request)

    def _ConvertKelvinToCelcius(self, temp):
        return temp - 273.15
