import sys
import json
import datetime
import os
from configparser import ConfigParser
from pylinky import LinkyClient
from influxdb import InfluxDBClient


def get_login_details ():
    parser = ConfigParser()
    parser.read('secret.ini')
    if parser.has_section("linky"):
        username = parser.get("linky", "username")
        password = parser.get("linky", "password")
    else:
        username = ""
        password = ""
        exit(-1)
    if parser.has_section("influxdb"):
        INFLUXDB_ADDRESS = parser.get("influxdb", "INFLUXDB_ADDRESS")
        INFLUXDB_USER = parser.get("influxdb", "INFLUXDB_USER")
        INFLUXDB_PASSWORD = parser.get("influxdb", "INFLUXDB_PASSWORD")
    else:
        INFLUXDB_ADDRESS = ""
        INFLUXDB_USER = ""
        INFLUXDB_PASSWORD = ""
        exit(-1)

    return username, password, INFLUXDB_ADDRESS, INFLUXDB_USER, INFLUXDB_PASSWORD


def linky_day_to_influxdb_point(linky_day, influxdb_client, location="beaumont"):
    """
    Convert the linky day results to the influx db

    :param linky_day: dict
    :param influxdb_client: InfluxDBClient
    :return:
    """
    influx_points = []
    if "data" not in linky_day:
        return None
    cur_day = datetime.datetime.strptime(linky_day["periode"]["dateDebut"], "%d/%m/%Y")
    if linky_day["period_type"] != "hourly":
        raise Exception("Input data is not in hourly format")

    for dp in linky_day["data"]:
        if dp["ordre"] <= 48:
            offset_time = datetime.timedelta(hours=int((dp["ordre"]-1)/2), minutes=((dp["ordre"]-1) % 2)*30)
            dp_time = cur_day + offset_time
            dp_kw = float(dp["valeur"])
            json_point = {
                'measurement': "consumption_kw",
                'tags': {
                    'location': location
                },
                'fields': {
                    'value': dp_kw
                },
                'time': datetime.datetime.strftime(dp_time, "%Y-%m-%dT%H:%M:%SZ"),
            }
            influx_points.append(json_point)

    if not influxdb_client.ping():
        _init_influxdb_database(influxdb_client)

    try:
        res = influxdb_client.write_points(influx_points)
    except Exception as e:
        print("ERROR: {}".format(e))
        return False
    else:
        return res


def get_daily_details(client, day, to_json_file=True):
    """
    Get the details of a day and return as a json ojects
    :type client: LinkyClient
    :type day: str
    :param to_json_file:
    :return:
    """
    start_date = day
    dir_name = "json_out"
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name, 755)

    st = datetime.datetime.strptime(start_date, "%d %b %Y")
    extra_days = datetime.timedelta(days=1)  # For whatever reason you have to ask for two days
    et = datetime.datetime.strptime(start_date, "%d %b %Y") + extra_days
    #print("Downloading {}".format(st))
    json_output = client.get_data_per_period(period_type="hourly", start=st, end=et)
    if to_json_file:
        jf = open("{}/{:04d}_{:02d}_{:02d}.json".format(dir_name, st.year, st.month, st.day), mode="w")
        jf.write(json.dumps(json_output, indent=2))
        jf.close()

    return json_output


def _init_influxdb_database(influxdb_client):
    """
    Connect to an influx database
    :param influxdb_client:
    :return:
    """
    INFLUXDB_DATABASE = 'home_db'

    databases = influxdb_client.get_list_database()
    print("Connected to influx database")
    if len(list(filter(lambda x: x['name'] == INFLUXDB_DATABASE, databases))) == 0:
        influxdb_client.create_database(INFLUXDB_DATABASE)
    influxdb_client.switch_database(INFLUXDB_DATABASE)


def main():

    username, password, INFLUXDB_ADDRESS, INFLUXDB_USER,  INFLUXDB_PASSWORD  = get_login_details()

    client = LinkyClient(username, password)
    influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)
    _init_influxdb_database(influxdb_client)

    try:
        client.login()
    except BaseException as exp:
        print("ERROR: {}".format(exp))
        exit(-1)
    else:
        client.fetch_data()
    # Loop through historical dates
    days = []
    start_day = "12 Nov 2019"
    for d in range(6):
        _d = datetime.datetime.strptime(start_day, "%d %b %Y") + datetime.timedelta(days=d)
        days.append(datetime.datetime.strftime(_d, "%d %b %Y"))

    for day in days:
        print("Getting details for {}".format(day))
        daily_details = get_daily_details(client, day)
        success = linky_day_to_influxdb_point(daily_details, influxdb_client)

        if success is None:
            print("WARN: No data to push")
        elif success:
            print("INFO: Pushed data to InfluxDB")
        else:
            print("ERROR: Failed to push data to InfluxDB")


if __name__== "__main__":
  main()