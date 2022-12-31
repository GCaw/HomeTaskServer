from datetime import datetime
import logging
from tasks.helper import IssueSqlRequest
from tasks.task_base import BaseTask

class WebTasksTask(BaseTask):
    def _add_init(self):
        """ Run additional startup tasks so as not to override init in child """
        self.last_result = ""
        self.last_temp = ""
        self.last_grg = ""
                
    def _intern_funct(self):
        """ This is where we put what we want the task to actually do """
        pass

    def save_data(self, type, data):
        ''' called externally to add a data entry in an adhoc manner'''
        if type == "TEMP":
            self._save_add_temp(data)
        elif type == "GRGST":
            self._save_garage_status(data)

        self.last_result = f"{self.last_temp}\n{self.last_grg}"

    def _save_add_temp(self, data):
        temp = float(data)
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        request = ("INSERT INTO `environment` (`uid`, `datetime`, `value`, `type`, `description`, `unit`) "
                    "VALUES (NULL, '%s','%f','5','bedroom_temp','degC')" % (now, temp))
        IssueSqlRequest(request)
        logging.info("New additional temperature: %f" % (temp))
        self.last_temp = f"TEMP: {temp} @ {now}"

    def _save_garage_status(self, data):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.last_grg = f"GRG: {data} @ {now}"