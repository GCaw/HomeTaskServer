import json
import plotly.express as px
import plotly.offline as po
from datetime import datetime
from os import path

from tasks.task_base import BaseTask
from tasks.config import WEATHER_API_ADDRESS, WEATHER_API_ZIPCODE, WEATHER_API_KEY, WEATHER_API_LAT, WEATHER_API_LONG
from tasks.helper import IssueHttpRequest, IssueSqlRequest, SelectSqlRequest

TEMP_GRAPH_PATH = path.join("generated_files", "temperatures.html")
TEMP_GRAPH_LONG_PATH = path.join("generated_files", "temperatures_long.html")
C02_GRAPH_PATH = path.join("generated_files", "co2.html")

class OutsideTempTask(BaseTask):
    """
    Task that fetches weather data from OpenWeather
    """
    def _add_init(self):
        self.counter = 30 # after how many calls should a week plot be updated
        
    def _intern_funct(self):
        self._get_temp()
        if (self.last_result == None):
            print("Ouside Temp: Not available")
        else:
            print("Ouside Temp: %.1f" % self.last_result)
            self._save_temp()
        self._plot_temp_press()
        self._plot_co2()
        self.counter += 1
        if (self.counter > 30):
            self._plot_temp_press_wk()
            self.counter = 0

        
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
            self.last_result = None
        else:
            self.last_result = self._ConvertKelvinToCelcius(result.json()['main']['temp'])
        
    def _save_temp(self):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        request = ("INSERT INTO `environment` (`uid`, `datetime`, `value`, `type`, `description`, `unit`) "
            "VALUES (NULL, '%s','%f','2','OutsideTemp','degC')" % (now, self.last_result))
        IssueSqlRequest(request)

    def _ConvertKelvinToCelcius(self, temp):
        return temp - 273.15
        
    def _plot_temp_press(days=1):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        request = ("SELECT * FROM `environment` WHERE `type` = 1 OR `type` = 2 OR `type` = 5 ORDER BY `datetime` DESC LIMIT 648")
        temps = SelectSqlRequest(request)

        request = ("SELECT * FROM `environment` WHERE `type` = 3 ORDER BY `datetime` DESC LIMIT 288")
        ind_press = SelectSqlRequest(request)

        fig = px.scatter(x=[a[1] for a in temps],y=[b[2] for b in temps], color=[c[4] for c in temps])
        po.plot(fig, filename=TEMP_GRAPH_PATH,auto_open=False)
        
    def _plot_temp_press_wk(weeks=1):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        request = ("SELECT * FROM `environment` WHERE `type` = 1 OR `type` = 2 OR `type` = 5 ORDER BY `datetime` DESC LIMIT 4536")
        temps = SelectSqlRequest(request)


        fig = px.scatter(x=[a[1] for a in temps],y=[b[2] for b in temps], color=[c[4] for c in temps])
        po.plot(fig, filename=TEMP_GRAPH_LONG_PATH,auto_open=False)

    def _plot_co2(days=1):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        request = ("SELECT * FROM `environment` WHERE `type` = 4 ORDER BY `datetime` DESC LIMIT 288")
        c02 = SelectSqlRequest(request)

        fig = px.scatter(x=[a[1] for a in c02],y=[b[2] for b in c02], color=[c[4] for c in c02])
        po.plot(fig, filename=C02_GRAPH_PATH,auto_open=False)