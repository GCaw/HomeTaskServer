import json
import plotly.express as px
import plotly.offline as po
from datetime import datetime, timedelta
from time import altzone
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
        self._plot_temp_press(TEMP_GRAPH_PATH)
        self._plot_co2()
        self.counter += 1
        if (self.counter > 30):
            self._plot_temp_press(TEMP_GRAPH_LONG_PATH, 7)
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
        
    def _plot_temp_press(self, plot_path, days_back=1):
        start_time = datetime.utcnow() - timedelta(days=days_back)
        start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")

        # 1, 2, 5 are rasp_pi, internet weather, wifi_temp
        request = (f"SELECT * FROM `environment` WHERE (`type` = 1 OR `type` = 2 OR `type` = 5) AND `datetime` > '{start_time}' ORDER BY `datetime`")
        temps = SelectSqlRequest(request)

        # pressure not currently used
        request = (f"SELECT * FROM `environment` WHERE `type` = 3  AND `datetime` > '{start_time}' ORDER BY `datetime`")
        ind_press = SelectSqlRequest(request)

        fig = px.scatter(x=[(a[1] + self._offset_time()) for a in temps],y=[b[2] for b in temps], color=[c[4] for c in temps])
        new_names = {'inside_temp':'office', 'bedroom_temp':'lounge', 'OutsideTemp':'outside'}
        fig.for_each_trace(lambda t: t.update(name = new_names[t.name],
                                              legendgroup = new_names[t.name],
                                              hovertemplate = t.hovertemplate.replace(t.name, new_names[t.name])))
        po.plot(fig, filename=plot_path, auto_open=False)

    def _plot_co2(self, days_back=1):
        start_time = datetime.utcnow() - timedelta(days=days_back)
        start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
        request = (f"SELECT * FROM `environment` WHERE `type` = 4 AND `datetime` > '{start_time}' ORDER BY `datetime`")
        c02 = SelectSqlRequest(request)

        fig = px.scatter(x=[(a[1]+ self._offset_time()) for a in c02],y=[b[2] for b in c02], color=[c[4] for c in c02])
        po.plot(fig, filename=C02_GRAPH_PATH, auto_open=False)

    def _offset_time(self, hour_offset=None):
        if not hour_offset:
            offset = timedelta(seconds = -altzone)
        else:
            offset = timedelta(hours = hour_offset)
        return offset