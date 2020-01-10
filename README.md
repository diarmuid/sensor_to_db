# Read sensors and push to InfluxDB

I have an InfluxDB running remotely on AWS. These scrips are typically run on a raspberry pi with a number of
sensors attached

## sensor_to_db.py
Read a number of sensors are write the reads to InfluxDB
Run from a service defined by sensodb.service

## linky_to_db
Read electricity consumption from Enedis and write the readings to InfluxDB

# Deprecated
* edf_to_inflxu.py
* cleanup_influx.py