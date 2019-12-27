from ds18b20 import DS18B20
import adafruit_bmp280
import adafruit_mcp9808
import busio
import board


def i2c():
    return busio.I2C(board.SCL, board.SDA)


class Sensors(object):
    def __init__(self, type, i2c=None, prefix=""):
        self._type = None
        self.i2c = i2c
        self.sensor = None
        self._type = None
        self.type = type
        self.prefix = prefix
        self.parameters = []


    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value == "bmp280":
            if self.i2c is None:
                raise Exception("bmp280 requires an i2c bus")
            self.sensor = adafruit_bmp280.Adafruit_BMP280_I2C(self.i2c)
            self._type = value
        elif value == "DS18B20":
            self.sensor = DS18B20()
            self._type = value
        elif value == "mcp9808":
            if self.i2c is None:
                raise Exception("mcp9808 requires an i2c bus")
            self.sensor = adafruit_mcp9808.MCP9808(self.i2c)
            self._type = value
        else:
            raise Exception("Sensor not supported")

    def get_readings(self):
        if self.type == "bmp280":
            try:
                temp = self.sensor.temperature
                pressure = self.sensor.pressure
            except:
                return None
            else:
                return [("{}temperature".format(self.prefix), temp),
                    ("{}pressure".format(self.prefix), pressure)]
        elif self.type == "DS18B20":
            try:
                temp = self.sensor.get_temperature()
            except:
                return None
            else:
                return [("{}temperature".format(self.prefix), temp)]
        elif self.type == "mcp9808":
            try:
                temp = self.sensor.temperature
            except:
                return None
            else:
             return [("{}temperature".format(self.prefix), temp)]

