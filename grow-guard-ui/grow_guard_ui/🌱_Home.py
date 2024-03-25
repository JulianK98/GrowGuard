import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB 
TOKEN = "SWMjXUZ1cooTaJASEU8Tiqv4pc6zFJMsXoGO05q46O-5cR1gn4VS7ZnlEK7eELFfc2EwNcRps7A-hbkvoN3XlQ=="
ORG = "GrowGuard"
URL = "http://192.168.2.140:8086"
BUCKET="growguard"

def load_data(client: InfluxDBClient) -> pd.DataFrame:
    query_api = client.query_api()

    query = f"""from(bucket: "{BUCKET}")
    |> range(start: -10m)
    |> filter(fn: (r) => r._measurement == "home")"""
    tables = query_api.query(query, org="GrowGuard")

    return tables
            
def measurement_change():
    print(f"Value change: ")

if __name__ == "__main__":
    influxdb_client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
    
    st.set_page_config(page_title="Grow Guard", page_icon="🌵")
    st.title("Grow Guard - Smart Irrigation")

    # Settings container
    with st.container(border=True):
        st.subheader("Settings")
        
        auto_irrigation_prev = True
        auto_irrigation = st.toggle("Automatic Irrigation", auto_irrigation_prev)
        measurement_intervall = st.selectbox("Measurement Intervall [s]", [1, 5, 10, 30], on_change=measurement_change)

        

    # Mini dashboard container 
    with st.container(border=True):
        st.subheader("Current Sensor Values")
        
        col1, col2, col3 = st.columns(3)
        
        curr_temp = 23
        delta_temp = 2
        temp = col1.metric("Temperature", f"{curr_temp}°C", f"{delta_temp}°C", help="test")
        
        curr_hum = 84
        delta_hum = -3
        hum = col2.metric("Air Humidity", f"{curr_hum}%", f"{delta_hum}%")
        
        curr_soil_hum = 65
        delta_soil_hum = -4
        soil_hum = col3.metric("Soil Humidity", f"{curr_soil_hum}%", f"{delta_soil_hum}%")
        
        
    # Irrigation container 
    with st.container(border=True):
        st.subheader("Irrigation")
        
        col1, col2 = st.columns(2)
        
        timestamp = "10:43"
        last_irrigation = col1.metric("Last Irrigation", timestamp)
        
        count = 3
        irrigation_count = col2.metric("Irrigations Today", count)
        
        
        