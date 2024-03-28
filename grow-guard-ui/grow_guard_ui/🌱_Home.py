import streamlit as st
import pandas as pd
from datetime import datetime
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
    |> range(start: -80h)
    |> filter(fn: (r) => r._measurement == "home")
    |> last()
    """
    
    tables = query_api.query(query, org="GrowGuard")
    
    latest_values = {"time":tables[0].records[0].get_time()}
    for table in tables:
        for record in table.records:
            latest_values.update({record.get_field():record.get_value()})
    
    return latest_values

def get_irrigation_count(client: InfluxDBClient) -> dict:
    query_api = client.query_api()

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: today())
    |> filter(fn: (r) => r._measurement == "irrigation")
    |> filter(fn: (r) => r._field == "irrigation-done")
    |> count()
    """
    
    tables = query_api.query(query, org=ORG)
    
    values = {}
    for table in tables:
        for record in table.records:
            values.update({record.get_field():record.get_value()})
    
    return values["irrigation-done"]

def get_last_irrigation_time(client: InfluxDBClient) -> dict:
    query_api = client.query_api()

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: today())
    |> filter(fn: (r) => r._measurement == "irrigation")
    |> filter(fn: (r) => r._field == "irrigation-done")
    |> last()
    """
    
    tables = query_api.query(query, org=ORG)
    
    last_values = {"time":tables[0].records[0].get_time()}
    for table in tables:
        for record in table.records:
            last_values.update({record.get_field():record.get_value()})
    
    return last_values["time"]
    
def load_settings_data(client: InfluxDBClient) -> dict:
    query_api = client.query_api()

    query = f"""
    from(bucket: "{BUCKET}")
    |> range(start: -80h)
    |> filter(fn: (r) => r._measurement == "settings")
    |> last()
    """
    
    tables = query_api.query(query, org="GrowGuard")
    
    settings_values = {"time":tables[0].records[0].get_time()}
    for table in tables:
        for record in table.records:
            settings_values.update({record.get_field():record.get_value()})
    
    return settings_values

def write_settings_data(client: InfluxDBClient, param: str, value) -> None:
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    point = (
        Point("settings")
        .field(param, value)
    )
    
    write_api.write(bucket=BUCKET, org=ORG, record=point)

def send_irrigation_signal(client: InfluxDBClient) -> None:
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    point = (
        Point("irrigation")
        .field("start-irrigation", True)
    )
    
    write_api.write(bucket=BUCKET, org=ORG, record=point)
            
def measurement_intervall_change():
    write_settings_data(INFLUXDB_CLIENT, "measurement-intervall", st.session_state.meas)

def auto_irrigation_change():     
    write_settings_data(INFLUXDB_CLIENT, "auto-irrigation", st.session_state.auto)

def on_man_irr_click():
    send_irrigation_signal(INFLUXDB_CLIENT)


if __name__ == "__main__":
    
    # General settings
    st.set_page_config(page_title="Grow Guard", page_icon="🌵")
    st.title("Grow Guard - Smart Irrigation")
    
    # Load data from InfluxDB
    latest_data = load_sensors_data(INFLUXDB_CLIENT)
    settings_data = load_settings_data(INFLUXDB_CLIENT)
    irrigation_count = get_irrigation_count(INFLUXDB_CLIENT)
    last_irrigation_time = get_last_irrigation_time(INFLUXDB_CLIENT)
   
 
    # Irrigation container 
    with st.container(border=True):
        st.subheader("Irrigation")
        
        auto_irrigation = st.toggle("Automatic Irrigation", 
                                    settings_data["auto-irrigation"], 
                                    key="auto", 
                                    on_change=auto_irrigation_change)
        
        manual_irrigation = st.button("Manual Irrigation", 
                                      type="primary", 
                                      key="man_irr", 
                                      disabled=auto_irrigation,
                                      on_click=on_man_irr_click)
        
        col1, col2 = st.columns(2)
        
        last_irrigation = col1.metric("Last Irrigation", last_irrigation_time.strftime("%H:%M"))
        
        irrigation_count = col2.metric("Irrigations Today", irrigation_count)
        
    # Mini dashboard container 
    with st.container(border=True):
        st.subheader("Current Sensor Values")
        
        meas_interval_options = [1, 5, 10, 30] 
        measurement_intervall = st.selectbox("Measurement Intervall [s]", 
                                             meas_interval_options, 
                                             index=meas_interval_options.index(settings_data["measurement-intervall"]),
                                             key="meas",
                                             on_change=measurement_intervall_change)
        
        col1, col2 = st.columns(2)
        
        temp_value = latest_data["temperature"]
        temp = col1.metric("Temperature", f"{temp_value}°C")
        
        air_hum_value = latest_data["air-humidity"]
        air_hum = col2.metric("Air Humidity", f"{air_hum_value}%")
        
        air_pressure_value = latest_data["air-pressure"]
        air_pressure = col1.metric("Air Pressure", f"{air_pressure_value}bar")
        
        soil_hum_value = latest_data["soil-humidity"]
        soil_hum = col2.metric("Soil Humidity", f"{soil_hum_value}%")
        
        
    # Cyclic sensor value update
    # while True:
    #     latest_data = load_latest_data(influxdb_client)
    #     sleep(2)
        