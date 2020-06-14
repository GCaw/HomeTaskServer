import json
import serial
from datetime import datetime

from tasks.task_base import GenericTask
from tasks.helper import IssueSqlRequest

try:
    from tasks.i2ctemp import bmp180
except ModuleNotFoundError:
    bmp180 = None
    print("Running mock bmp180")    
    
class IndoorTempPressTask(GenericTask):
    """
    Task to read data from i2c connected Temperature/Pressure sensor
    """
    def _add_init(self):
        try:
            self.sensor = bmp180()
        except:
            # we've already tried to import the bmp and failed
            pass
            
    def _intern_funct(self):
        t_and_p = None
        try:
            t_and_p = self.sensor.GetTAndP()
            self.last_result = "Inside Temp: %.1f\nInside Press: %.1f" % (t_and_p[0], t_and_p[1])
        except Exception as e:
            self.last_result = "Inside TempPress: Error accessing bmp180 sensor"
            print (e)
        
        if t_and_p:
            self._save_temp_press(t_and_p)

        print(self.last_result)
        
    def _save_temp_press(self, tnp):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        request = ("INSERT INTO `environment` (`uid`, `datetime`, `value`, `type`, `description`, `unit`) "
                    "VALUES (NULL, '%s','%f','1','inside_temp','degC')" % (now, tnp[0]))
        IssueSqlRequest(request)
        
        request = ("INSERT INTO `environment` (`uid`, `datetime`, `value`, `type`, `description`, `unit`) "
                    "VALUES (NULL, '%s','%f','3','inside_press','degC')" % (now, tnp[1]))
        IssueSqlRequest(request)

class IndoorCO2(HomeTask):
    """
    Task to read serial data from attached C02 sensor
    """
    def _add_init(self):
        """ Run additional startup tasks so as not to override init in child """
        pass
                
    def _intern_funct(self):
        self.last_result = self._read_co2()

        if not (self.last_result == 0):
            self._save_co2(self.last_result)

    def _read_co2(self):
        try:
            ser = serial.Serial('/dev/serial0', 9600, timeout=1)
            get_co2_cmd = b'\xFF\x01\x86\x00\x00\x00\x00\x00\x79'
            ser.write(get_co2_cmd)

            res = ser.read(9)
            # We should check the CRC, yolo
            co2 = res[2] * 256 + res[3]

        except Exception as e:
            co2 = 0
            print("CO2 Serial error")
            print(e)

        try:
            ser.close()
        except Exception as e:
            print("CO2 Serial error")
            print(e)

        print("CO2 sensor: %s" % (co2))

        return co2

    def _save_co2(self, co2):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        request = ("INSERT INTO `environment` (`uid`, `datetime`, `value`, `type`, `description`, `unit`) "
                    "VALUES (NULL, '%s','%f','4','inside_co2','degC')" % (now, co2))
        IssueSqlRequest(request)