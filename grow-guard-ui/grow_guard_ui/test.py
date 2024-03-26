import pandas as pd
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB 
TOKEN = "SWMjXUZ1cooTaJASEU8Tiqv4pc6zFJMsXoGO05q46O-5cR1gn4VS7ZnlEK7eELFfc2EwNcRps7A-hbkvoN3XlQ=="
ORG = "GrowGuard"
URL = "http://192.168.2.140:8086"
BUCKET="growguard"

def load_data(client: InfluxDBClient) -> dict:
    query_api = client.query_api()

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: -12h)
    |> filter(fn: (r) => r._measurement == "settings")
    |> last()
    """
    
    tables = query_api.query(query, org="GrowGuard")
    
    last_values = {"time":tables[0].records[0].get_time()}
    for table in tables:
        for record in table.records:
            last_values.update({record.get_field():record.get_value()})
    
    return last_values

def write_data(client) -> None:
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    point = (
        Point("settings")
        .field("auto-irrigation", True)
        # .field("measurement-intervall", 5)
    )
    
    write_api.write(bucket=BUCKET, org=ORG, record=point)
        
if __name__ == "__main__":
    influxdb_client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
    
    write_data(influxdb_client)
    
    settings_data = load_data(influxdb_client)
    print(settings_data)
    
    meas_interval_options = [1, 5, 10, 30]
    print(meas_interval_options.index(settings_data["measurement-intervall"]))
    