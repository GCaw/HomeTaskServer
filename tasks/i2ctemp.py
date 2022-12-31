import logging
import smbus
from time import sleep

DEVICE_BUS_ADDRESS = 0x77

class bmp180:
    """
    Class to read i2c data from BMP180 temp/pressure sensor and
     calulate readings based on internal calibration.
    """
    def __init__(self):
        self.cal_data = {}
        self.bus = smbus.SMBus(1)
        
    def GetCalData(self):
        self.Read16bitCalVal('ac1',0xAA, True)
        self.Read16bitCalVal('ac2',0xAC, True)
        self.Read16bitCalVal('ac3',0xAE, True)
        self.Read16bitCalVal('ac4',0xB0, False)
        self.Read16bitCalVal('ac5',0xB2, False)
        self.Read16bitCalVal('ac6',0xB4, False)
        self.Read16bitCalVal('b1', 0xB6, True)
        self.Read16bitCalVal('b2', 0xB8, True)
        self.Read16bitCalVal('mb', 0xBA, True)
        self.Read16bitCalVal('mc', 0xBC, True)
        self.Read16bitCalVal('md', 0xBE, True)

    def Read16bitCalVal(self,vari, address, signed):
        val1 = self.bus.read_byte_data(DEVICE_BUS_ADDRESS, address)
        val2 = self.bus.read_byte_data(DEVICE_BUS_ADDRESS, address+1)
        value = (val1 << 8) + val2

        if (value == 0 or value == 65535):
            logging.error(f"error {vari} = {value}")

        #shoddy way to convert if it's supposed to be a negative number
        if ((value >= 32768) and signed):
            value -= 32768*2
            
        self.cal_data[vari] = value

    def GetRawTemp(self):
        self.bus.write_byte_data(DEVICE_BUS_ADDRESS, 0xF4, 0x2E)
        sleep(0.1)
        raw_temp = (self.bus.read_byte_data(DEVICE_BUS_ADDRESS, 0xF6) << 8) + self.bus.read_byte_data(DEVICE_BUS_ADDRESS, 0xF7)
        return raw_temp

    def GetRawPress(self,oss):
        self.bus.write_byte_data(DEVICE_BUS_ADDRESS, 0xF4, (0x34 + (oss << 6)))
        sleep(0.1)
        raw_press = ((self.bus.read_byte_data(DEVICE_BUS_ADDRESS, 0xF6) << 16) + (self.bus.read_byte_data(DEVICE_BUS_ADDRESS, 0xF7) << 8) + self.bus.read_byte_data(DEVICE_BUS_ADDRESS, 0xF8)) >> (8-oss)
        return raw_press

    def CalculateTemp(self):
        self.cal_data['x1'] = (self.GetRawTemp() - self.cal_data['ac6']) * self.cal_data['ac5'] / (2**15)
        self.cal_data['x2'] = self.cal_data['mc'] * (2**11) / (self.cal_data['x1'] + self.cal_data['md'])
        self.cal_data['b5'] = self.cal_data['x1'] + self.cal_data['x2']
        temp10 = (self.cal_data['b5'] + 8) / (2**4)
        return temp10/10.0

    def CalculatePress(self,oss):
        self.cal_data['b6'] = self.cal_data['b5'] - 4000
        self.cal_data['x1'] = (self.cal_data['b2'] * (self.cal_data['b6']*self.cal_data['b6'] / (2**12)))/(2**11)
        self.cal_data['x2'] = self.cal_data['ac2'] * self.cal_data['b6'] / (2**11)
        self.cal_data['x3'] = self.cal_data['x1'] + self.cal_data['x2']
        self.cal_data['b3'] = ((int(self.cal_data['ac1']*4+self.cal_data['x3']) << oss) +2) / 4
        self.cal_data['x1'] = self.cal_data['ac3'] *self.cal_data['b6'] / (2**13)
        self.cal_data['x2'] = (self.cal_data['b1'] * (self.cal_data['b6']*self.cal_data['b6']/(2**12)))/(2**16)
        self.cal_data['x3'] = ((self.cal_data['x1'] + self.cal_data['x2'])+2)/(2**2)
        self.cal_data['b4'] = self.cal_data['ac4'] * (self.cal_data['x3'] + 32768)/(2**15) #WARNING SHOULD BE unsigned long
        self.cal_data['b7'] = (self.GetRawPress(oss) - self.cal_data['b3']) * (50000 >> oss) #WARNING SHOULD BE unsigned long
        
        if (self.cal_data['b7'] < 0x8000000000):
            pressure = (self.cal_data['b7'] * 2) / self.cal_data['b4']
        else:
            pressure = (self.cal_data['b7'] / self.cal_data['b4']) * 2
            
        self.cal_data['x1'] = (pressure / (2**8)) * (pressure / (2**8))
        self.cal_data['x1'] = (self.cal_data['x1'] * 3038) / (2**16)
        self.cal_data['x2'] = (-7357 * pressure) / (2**16)
        pressure = pressure + (self.cal_data['x1'] + self.cal_data['x2'] +3791) / (2**4)
        
        return pressure/100.0

    def CalculateAltitiude(self,press):
        return 44330 * (1-(press / 1013.25)**(1/5.255)) #press in hpa

    def GetTAndP(self):
        self.GetCalData()
        temp = self.CalculateTemp()
        press = self.CalculatePress(2)
        return [temp, press]

if __name__=="__main__":
    sensor = bmp180()
    print (sensor.GetTAndP())