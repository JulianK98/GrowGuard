import pandas as pd
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB 
TOKEN = "SWMjXUZ1cooTaJASEU8Tiqv4pc6zFJMsXoGO05q46O-5cR1gn4VS7ZnlEK7eELFfc2EwNcRps7A-hbkvoN3XlQ=="
ORG = "GrowGuard"
URL = "http://192.168.2.140:8086"
BUCKET="growguard"

def get_data(client: InfluxDBClient) -> dict:
    query_api = client.query_api()

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: -100000h)
    |> filter(fn: (r) => r._measurement == "irrigation")
    |> filter(fn: (r) => r._field == "start-irrigation")
    |> last()
    """

    
    tables = query_api.query(query, org=ORG)

    last_values = {}
    if tables != []:    
        last_values.update({"time":tables[0].records[0].get_time()})
        for table in tables:
            for record in table.records:
                last_values.update({record.get_field():record.get_value()})
    
    return last_values

def write_data(client) -> None:
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    point = (
        Point("irrigation")
        .field("start-irrigation", True)
    )
    
    write_api.write(bucket=BUCKET, org=ORG, record=point)
        

def get_irrigation_count(client: InfluxDBClient) -> int:
    query_api = client.query_api()

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: today())
    |> filter(fn: (r) => r._measurement == "irrigation")
    |> filter(fn: (r) => r._field == "irrigation-done")
    |> count()
    """
    
    tables = query_api.query(query, org=ORG)

    if tables != []:
        count = tables[0].records[0].get_value()
    else:
        count = 0
        
    return tables
    
    
    
    
if __name__ == "__main__":
    influxdb_client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
    
    
    data = get_data(influxdb_client)
    # print(data.strftime("%H:%M"))
    print(data)
    
    