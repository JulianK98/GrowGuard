import os
import influxdb_client
import time
from random import randrange
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# TOKEN = os.environ.get("INFLUXDB_TOKEN")
TOKEN = "SWMjXUZ1cooTaJASEU8Tiqv4pc6zFJMsXoGO05q46O-5cR1gn4VS7ZnlEK7eELFfc2EwNcRps7A-hbkvoN3XlQ=="
ORG = "GrowGuard"
URL = "http://192.168.2.140:8086"
BUCKET="growguard"

INTERVAL = 1


if __name__ == "__main__":
    write_client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
    

    write_api = write_client.write_api(write_options=SYNCHRONOUS)
    
    while True:
        point = (
            Point("home")
            .tag("room", "conservatory")
            .field("temperature", randrange(0, 30))
            .field("air-humidity", randrange(60, 100))
            .field("air-pressure", randrange(970, 1200))
            .field("soil-humidity", randrange(40, 70))
        )
        
        try:
            write_api.write(bucket=BUCKET, org=ORG, record=point)
        except Exception as e:
            print(e)
        
        time.sleep(INTERVAL) 
