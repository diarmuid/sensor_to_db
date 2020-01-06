from influxdb import InfluxDBClient
from configparser import ConfigParser
import datetime


class SensorData(object):
    def __init__(self, location, measurement, value, time=None):
        self.location = location
        self.measurement = measurement
        self.value = value
        if time is None:
            self.time = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%dT%H:%M:%SZ"),
        else:
            self.time = time

    def to_json(self):
        json_body = {
                'measurement': self.measurement,
                'tags': {
                    'location': self.location
                },
                'fields': {
                    'value': self.value
                },
                'time': self.time,
            }
        return json_body


class SensorInfluxDB(InfluxDBClient):

    def __init__(self, inifile):
        addr, user, pw = SensorInfluxDB.get_login_details(inifile)
        if addr is None:
            raise Exception("No login details in the ini file")
        super(SensorInfluxDB, self).__init__(addr, 8086, user, pw, None)
        self._init_influxdb_database()
        self.points = []

    def _init_influxdb_database(self):
        """
        Connect to an influx database
        :param influxdb_client:
        :return:
        """
        INFLUXDB_DATABASE = 'home_db'
        databases = self.get_list_database()
        if len(list(filter(lambda x: x['name'] == INFLUXDB_DATABASE, databases))) == 0:
            self.create_database(INFLUXDB_DATABASE)
        self.switch_database(INFLUXDB_DATABASE)

    @staticmethod
    def get_login_details(inifile):
        parser = ConfigParser()
        parser.read(inifile)
        if parser.has_section("influxdb"):
            influxdb_address = parser.get("influxdb", "INFLUXDB_ADDRESS")
            influxdb_user = parser.get("influxdb", "INFLUXDB_USER")
            influxdb_password = parser.get("influxdb", "INFLUXDB_PASSWORD")
            return influxdb_address, influxdb_user, influxdb_password
        else:
            return None, None, None

    def cache_and_send(self, point):
        self.points.append(point)
        if len(self.points) % 10 == 0:
            json_points = []
            for p in self.points:
                json_points.append(p.to_json())

            if not self.ping():
                self._init_influxdb_database()

            if self.write_points(json_points):
               self.points = []