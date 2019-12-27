"""
Read the sensors and push the data to a database
"""

import Sensors
import SensorInfluxDB
import time
import argparse

parser = argparse.ArgumentParser(description='Read a sensor and push to the database')
parser.add_argument('connected_sensors', type=str, nargs='+', choices=["bmp280", "DS18B20"],
                    help='sensor type connected')
parser.add_argument('--location', type=str, required=True, help="The location of the sensor")
parser.add_argument('--rate', type=int, required=False, default=2, help="The rate in Hz to read the sensor")
args = parser.parse_args()

# location
secret = "secret.ini"

i2c_bus = Sensors.i2c()
db = SensorInfluxDB.SensorInfluxDB(inifile=secret)
sensors = []
for sensor_type in args.connected_sensors:
    sensor = Sensors.Sensors(type=sensor_type, i2c=i2c_bus)
    sensors.append(sensor)

while True:
    for sensor in sensors:
        for reading in sensor.get_readings():
            data_point = SensorInfluxDB.SensorData(location=args.location, measurement=reading[0], value=reading[1])
            db.cache_and_send(data_point)
    time.sleep(2)