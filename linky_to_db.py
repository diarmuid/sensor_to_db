# Pull hourly consumption usage from ENEDIS and push to an InfluxDB data base
# Put this in a crontabl job to be run after midnight. It will pull down the
# data from the previous night and push it to Influxdb


import SensorInfluxDB
import datetime
from configparser import ConfigParser
from pylinky import LinkyClient
import argparse
import json
import logging

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

    def get_daily_details(self, day, location, to_json_file=None):
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
        if to_json_file:
            jf = open("{}/{:04d}_{:02d}_{:02d}.json".format(to_json_file, st.year, st.month, st.day), mode="w")
            jf.write(json.dumps(json_output, indent=2))
            jf.close()

        influx_points = []
        for dp in json_output["data"]:
            if dp["ordre"] <= 48:
                offset_time = datetime.timedelta(hours=int((dp["ordre"] - 1) / 2), minutes=((dp["ordre"] - 1) % 2) * 30)
                dp_time = st + offset_time
                dp_kw = float(dp["valeur"])
                l_p = SensorInfluxDB.SensorData(location, "consumption_kw", dp_kw, datetime.datetime.strftime(dp_time, "%Y-%m-%dT%H:%M:%SZ"))
                influx_points.append(l_p)
        return influx_points


parser = argparse.ArgumentParser(description='Read a electricity sensor and push to the database')
parser.add_argument('--secret', type=str, required=True, help="path to the secret file")
args = parser.parse_args()

logging.basicConfig(level=logging.INFO)
db = SensorInfluxDB.SensorInfluxDB(inifile=args.secret)
db.connect_to_db()

username, password = LinkyClientExt.get_login_details(args.secret)
client = LinkyClientExt(username, password)
try:
    client.login()
except BaseException as exp:
    print("ERROR: {}".format(exp))
    exit(-1)
else:
    client.fetch_data()

yesterday = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(days=1), "%d %b %Y")
db.cache_and_send(client.get_daily_details(yesterday, "beaumont", "dump"))