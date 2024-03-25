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
            


if __name__ == "__main__":
    influxdb_client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
    
    st.set_page_config(page_title="Grow Guard", page_icon="🌵")
    st.title("Dashboard")
    
    
