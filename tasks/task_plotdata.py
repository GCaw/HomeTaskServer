import logging
import plotly.express as px
import plotly.offline as po
from datetime import datetime, timedelta
import time
from os import path

from tasks.task_base import BaseTask
from tasks.helper import SelectSqlRequest

TEMP_GRAPH_PATH = path.join("generated_files", "temperatures.html")
TEMP_GRAPH_LONG_PATH = path.join("generated_files", "temperatures_long.html")
C02_GRAPH_PATH = path.join("generated_files", "co2.html")
PRESS_GRAPH_PATH = path.join("generated_files", "pressures.html")

class PlotDataTask(BaseTask):
    """
    Task that plots data from database

    Database value types
     1 rasp_pi temp
     2 internet temp
     3 rasp_pi press
     4 rasp_pi c02
     5 wifi_temp

    """
    def _add_init(self):
        self.counter = 30 # after how many calls should a week plot be updated
        
    def _intern_funct(self):
        logging.info("Plot Temperature and CO2 data")
        self._plot_temp(TEMP_GRAPH_PATH)
        self._plot_co2()
        self.counter += 1
        self.last_result = "Temp & CO2"
        if (self.counter > 30):
            logging.info("Plot long Temperature data")
            self._plot_temp(TEMP_GRAPH_LONG_PATH, 7)
            self._plot_pressure()
            self.counter = 0
            self.last_result += " & long Temp"
        self.last_result += " plots generated"
        
    def _plot_temp(self, plot_path, days_back=1):
        ''' plot the temperature '''
        start_time = datetime.utcnow() - timedelta(days=days_back)
        start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")

        request = (f"SELECT * FROM `environment` WHERE (`type` = 1 OR `type` = 2 OR `type` = 5) AND `datetime` > '{start_time}' ORDER BY `datetime`")
        temps = SelectSqlRequest(request)

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

    def _plot_pressure(self, days_back=7):
        start_time = datetime.utcnow() - timedelta(days=days_back)
        start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
        request = (f"SELECT * FROM `environment` WHERE `type` = 3 AND `datetime` > '{start_time}' ORDER BY `datetime`")
        c02 = SelectSqlRequest(request)

        fig = px.scatter(x=[(a[1]+ self._offset_time()) for a in c02],y=[b[2] for b in c02], color=[c[4] for c in c02])
        po.plot(fig, filename=PRESS_GRAPH_PATH, auto_open=False)

    def _offset_time(self, hour_offset=None):
        ''' get a timedelta on which to offset the plotted data
            defaults to local timezone '''
        if not hour_offset:
            t = time.localtime()
            tz_offset = time.altzone
            if t.tm_isdst == 0:
                tz_offset = time.timezone

            offset = timedelta(seconds = -1*tz_offset)
        else:
            offset = timedelta(hours = hour_offset)
        return offset