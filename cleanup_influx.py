from configparser import ConfigParser
from pylinky import LinkyClient
from influxdb import InfluxDBClient
from edf_to_influx import get_login_details, _init_influxdb_database

username, password, INFLUXDB_ADDRESS, INFLUXDB_USER,  INFLUXDB_PASSWORD  = get_login_details()
influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)
_init_influxdb_database(influxdb_client)
query="select * from consumption_kw where time >= '2019-11-01T00:00:00Z' and time <= '2019-11-17T00:00:00Z'"
influxdb_client.query(query)