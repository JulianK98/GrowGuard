import sys
from datetime import datetime
from time import sleep
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


# Check if UI should be started in dev mode
if len(sys.argv) >= 2:
    if sys.argv[1] == "dev":
        DEV = True
    else:
        DEV = False
else:
    DEV = False
    

# InfluxDB
ORG = "GrowGuard"
BUCKET = "growguard"
if DEV:
    TOKEN = "ONRceIkyGlQs6jSymPUaFQT8yvViUtxCINTv9cHrrb7fdUP0FjJMbz5Tb3O4kl9NT06VjiS2zImcM0-5bevxGg=="
    URL = "http://192.168.2.140:8086"    
else:
    TOKEN = "GVaqO3_LMrj-6_-tHNGDP3eIXQj5yR85B4IfSFEQZoVhB923C09Ys70VorDIVKAxogWQ-loHFNmIEnzrFog0Yw=="
    URL = "http://192.168.2.201:8086"

INFLUXDB_CLIENT = InfluxDBClient(url=URL, token=TOKEN, org=ORG)



def get_soil_humidity(client: InfluxDBClient) -> float:
    query_api = client.query_api()

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: -1h)
    |> filter(fn: (r) => r._measurement == "sensors")
    |> filter(fn: (r) => r._field == "soil-humidity")
    |> median()
    """

    tables = query_api.query(query, org=ORG)

    if tables != []:
        soil_hum = tables[0].records[0].get_value()
    else:
        soil_hum = 100
        
    return soil_hum

def last_irrigation(client: InfluxDBClient, limit: int) -> bool:
    query_api = client.query_api()

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: -{limit}m)
    |> filter(fn: (r) => r._measurement == "irrigation")
    |> filter(fn: (r) => r._field == "irrigation-done")
    |> last()
    """

    tables = query_api.query(query, org=ORG)

    if tables == []:
        return True
    else:
        return False

def auto_mode(client: InfluxDBClient) -> bool:
    query_api = client.query_api()

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: -1000000h)
    |> filter(fn: (r) => r._measurement == "settings")
    |> filter(fn: (r) => r._field == "auto-irrigation")
    |> last()
    """

    tables = query_api.query(query, org=ORG)

    if tables != []:
        auto_mode = tables[0].records[0].get_value()
    else:
        auto_mode = False

    return auto_mode

def get_auto_mode_config(client: InfluxDBClient) -> dict:
    query_api = client.query_api()

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: -1000000h)
    |> filter(fn: (r) => r._measurement == "settings")
    |> filter(fn: (r) => r._field == "last-irr-limit" or r._field == "pulse-length" or r._field == "soil-hum-limit")
    |> last()
    """

    tables = query_api.query(query, org=ORG)

    if tables != []:
        settings = {}
        for table in tables:
            settings.update({table.records[0].get_field(): table.records[0].get_value()})
    else:
        settings = {
            "last-irr-limit": 5.0,
            "soil-hum-limit": 50,
            "pulse-length": 5,
        }

    return settings       

def send_irrigation_signal(client: InfluxDBClient) -> None:
    write_api = client.write_api(write_options=SYNCHRONOUS)

    point = Point("irrigation").field("start-irrigation", True)

    write_api.write(bucket=BUCKET, org=ORG, record=point)

def write_pulse_length(client: InfluxDBClient, pulse_length: int) -> None:
    write_api = client.write_api(write_options=SYNCHRONOUS)

    point = Point("irrigation").field("pulse-length", pulse_length)

    write_api.write(bucket=BUCKET, org=ORG, record=point)


def main():
    
    while True:
        
        if auto_mode(INFLUXDB_CLIENT) == True:
            auto_mode_config = get_auto_mode_config(INFLUXDB_CLIENT)
            
            soil_humidity = get_soil_humidity(INFLUXDB_CLIENT)
            print(soil_humidity)
            
            last_irr = last_irrigation(INFLUXDB_CLIENT, int(auto_mode_config["last-irr-limit"]*60))
            print(last_irr)
            
            if last_irr == True and soil_humidity <= auto_mode_config["soil-hum-limit"]:
                write_pulse_length(INFLUXDB_CLIENT, auto_mode_config["pulse-length"])
                send_irrigation_signal(INFLUXDB_CLIENT)
                print("Irrigation initiated!")
                
        # Repeat every 10 minutes        
        sleep(600)

def test():
    print(auto_mode(INFLUXDB_CLIENT))
    print(get_auto_mode_config(INFLUXDB_CLIENT))
    print(get_soil_humidity(INFLUXDB_CLIENT))
    print(last_irrigation(INFLUXDB_CLIENT, 100000))
    

if __name__ == "__main__":
    main()
    