import SensorInfluxDB
import datetime
from configparser import ConfigParser
from pylinky import LinkyClient


class LinkyClientExt(LinkyClient):
    @staticmethod
    def get_login_details(inifile):
        parser = ConfigParser()
        parser.read(inifile)
        if parser.has_section("linky"):
            user = parser.get("linky", "username")
            password = parser.get("linky", "password")
            return user, password
        else:
            return None, None

    def get_daily_details(self, day, location):
        """
        Get the details of a day and return as a json ojects
        :type client: LinkyClient
        :type day: str
        :param to_json_file:
        :return:
        """
        start_date = day

        st = datetime.datetime.strptime(start_date, "%d %b %Y")
        extra_days = datetime.timedelta(days=1)  # For whatever reason you have to ask for two days
        et = datetime.datetime.strptime(start_date, "%d %b %Y") + extra_days
        # print("Downloading {}".format(st))
        json_output = self.get_data_per_period(period_type="hourly", start=st, end=et)
        influx_points = []
        for dp in json_output["data"]:
            if dp["ordre"] <= 48:
                offset_time = datetime.timedelta(hours=int((dp["ordre"] - 1) / 2), minutes=((dp["ordre"] - 1) % 2) * 30)
                dp_time = st + offset_time
                dp_kw = float(dp["valeur"])
                l_p = SensorInfluxDB.SensorData(location, "consumption_kw", dp_kw, datetime.datetime.strftime(dp_time, "%Y-%m-%dT%H:%M:%SZ"))
                influx_points.append(l_p)
        return influx_points


db = SensorInfluxDB.SensorInfluxDB(inifile="secret.ini")
username, password = LinkyClientExt.get_login_details("secret.ini")
client = LinkyClientExt(username, password)
try:
    client.login()
except BaseException as exp:
    print("ERROR: {}".format(exp))
    exit(-1)
else:
    client.fetch_data()

yesterday = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(days=1), "%d %b %Y")
for point in client.get_daily_details(yesterday, "beaumont"):
    db.cache_and_send(point)