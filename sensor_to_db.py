"""
Read the sensors and push the data to a database
"""

import Sensors
import SensorInfluxDB
import time
import argparse
import logging

parser = argparse.ArgumentParser(description='Read a sensor and push to the database')
parser.add_argument('--sensor', type=str, required=True, choices=["bmp280", "DS18B20"],
                    action="append", help='sensor type connected')
parser.add_argument('--location', type=str, required=True, help="The location of the sensor")
parser.add_argument('--rate', type=int, required=False, default=1, help="The rate in Hz to read the sensor")
parser.add_argument('--debug', action="store_true", help="debug mode ")
args = parser.parse_args()

# location
secret = "secret.ini"
# Logging level
if args.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# Create i2c
i2c_bus = Sensors.i2c()
db = SensorInfluxDB.SensorInfluxDB(inifile=secret)

sensors = []
for sensor_type in args.sensor:
    logging.debug("Creating sensor type {}".format(sensor_type))
    sensor = Sensors.Sensors(type=sensor_type, i2c=i2c_bus)
    if sensor_type == "DS18B20":
        sensor.prefix = "outside"
    sensors.append(sensor)

db.cache_count = 10 * len(sensors)
while True:
    for sensor in sensors:
        for reading in sensor.get_readings():
            data_point = SensorInfluxDB.SensorData(location=args.location, measurement=reading[0], value=reading[1])
            logging.debug("Read {}".format(repr(data_point)))
            db.cache_and_send(data_point)
    time.sleep(args.rate)