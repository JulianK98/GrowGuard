import streamlit as st
import pandas as pd
from time import sleep
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB 
TOKEN = "SWMjXUZ1cooTaJASEU8Tiqv4pc6zFJMsXoGO05q46O-5cR1gn4VS7ZnlEK7eELFfc2EwNcRps7A-hbkvoN3XlQ=="
ORG = "GrowGuard"
URL = "http://192.168.2.140:8086"
BUCKET="growguard"
INFLUXDB_CLIENT = InfluxDBClient(url=URL, token=TOKEN, org=ORG)



def load_sensors_data(client: InfluxDBClient) -> dict:
    query_api = client.query_api()

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: -12h)
    |> filter(fn: (r) => r._measurement == "home")
    |> last()
    """
    
    tables = query_api.query(query, org="GrowGuard")
    
    latest_values = {"time":tables[0].records[0].get_time()}
    for table in tables:
        for record in table.records:
            latest_values.update({record.get_field():record.get_value()})
    
    return latest_values

def load_settings_data(client: InfluxDBClient) -> dict:
    query_api = client.query_api()

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: -12h)
    |> filter(fn: (r) => r._measurement == "settings")
    |> last()
    """
    
    tables = query_api.query(query, org="GrowGuard")
    
    settings_values = {"time":tables[0].records[0].get_time()}
    for table in tables:
        for record in table.records:
            settings_values.update({record.get_field():record.get_value()})
    
    return settings_values

def write_settings_data(client, param: str, value) -> None:
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    point = (
        Point("settings")
        .field(param, value)
    )
    
    write_api.write(bucket=BUCKET, org=ORG, record=point)

            
def measurement_intervall_change():
    write_settings_data(INFLUXDB_CLIENT, "measurement-intervall", st.session_state.meas)

def auto_irrigation_change():
    write_settings_data(INFLUXDB_CLIENT, "auto-irrigation", st.session_state.auto)


if __name__ == "__main__":
    
    # General settings
    st.set_page_config(page_title="Grow Guard", page_icon="🌵")
    st.title("Grow Guard - Smart Irrigation")
    
    # Load data from InfluxDB
    latest_data = load_sensors_data(INFLUXDB_CLIENT)
    settings_data = load_settings_data(INFLUXDB_CLIENT)

    # Settings container
    with st.container(border=True):
        st.subheader("Settings")
        
        auto_irrigation = st.toggle("Automatic Irrigation", 
                                    settings_data["auto-irrigation"], 
                                    key="auto", 
                                    on_change=auto_irrigation_change)
        
        meas_interval_options = [1, 5, 10, 30] 
        measurement_intervall = st.selectbox("Measurement Intervall [s]", 
                                             meas_interval_options, 
                                             index=meas_interval_options.index(settings_data["measurement-intervall"]),
                                             key="meas",
                                             on_change=measurement_intervall_change)
        

    # Mini dashboard container 
    with st.container(border=True):
        st.subheader("Current Sensor Values")
        
        col1, col2 = st.columns(2)
        
        temp_value = latest_data["temperature"]
        temp = col1.metric("Temperature", f"{temp_value}°C")
        
        air_hum_value = latest_data["air-humidity"]
        air_hum = col2.metric("Air Humidity", f"{air_hum_value}%")
        
        air_pressure_value = latest_data["air-pressure"]
        air_pressure = col1.metric("Air Pressure", f"{air_pressure_value}bar")
        
        soil_hum_value = latest_data["soil-humidity"]
        soil_hum = col2.metric("Soil Humidity", f"{soil_hum_value}%")
        
        
    # Irrigation container 
    with st.container(border=True):
        st.subheader("Irrigation")
        
        col1, col2 = st.columns(2)
        
        timestamp = "10:43"
        last_irrigation = col1.metric("Last Irrigation", timestamp)
        
        count = 3
        irrigation_count = col2.metric("Irrigations Today", count)
        
        
    # Cyclic sensor value update
    # while True:
    #     latest_data = load_latest_data(influxdb_client)
    #     sleep(2)
        