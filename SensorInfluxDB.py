from influxdb import InfluxDBClient
from configparser import ConfigParser
import datetime
import logging
from collections import deque


class SensorData(object):
    def __init__(self, location, measurement, value, time=None):
        self.location = location
        self.measurement = measurement
        self.value = value
        if time is None:
            self.time = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%dT%H:%M:%SZ")
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

    def __repr__(self):
        return "Location:{} Measurement:{} Value:{} Time:{}".format(self.location, self.measurement, self.value, self.time)


MAX_POINTS_PER_ACCESS = 50


class SensorInfluxDB(InfluxDBClient):

    def __init__(self, inifile):
        addr, user, pw = SensorInfluxDB.get_login_details(inifile)
        if addr is None:
            raise Exception("No login details in the ini file")
        super().__init__(addr, 8086, user, pw, None)
        #self._init_influxdb_database()
        self.points = deque(maxlen=300)
        self.cache_count = 30

    def connect_to_db(self):
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

    def cache_and_send(self, points, no_cache=False):
        """
        Cache a point and send them when enough are cached
        :param point: list[int]
        :return:
        """
        self.points += points
        logging.debug("Total points = {}".format(len(self.points)))
        if (len(self.points) % self.cache_count == 0 and no_cache==False) or no_cache == True:
            json_points = []
            # Convert the points to json txt
            for p in self.points:
                json_points.append(p.to_json())
            #print("Sending points = {}".format(len(json_points)))
            # Now send them
            try:
                self.write_points(json_points, batch_size=MAX_POINTS_PER_ACCESS, time_precision="s")
            except Exception as e:
                # Try and connect and next time around upload the points
                logging.debug("Failed to connect to influx. ({}) Caching points".format(e))
                try:
                    self.connect_to_db()
                except:
                    pass
            else:
                # Clear the cache
                self.points = []
                for p in json_points:
                    logging.debug("Sent {} to influx".format(repr(p)))
