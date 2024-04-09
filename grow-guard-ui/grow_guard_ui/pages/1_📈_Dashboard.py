import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB
TOKEN = "SWMjXUZ1cooTaJASEU8Tiqv4pc6zFJMsXoGO05q46O-5cR1gn4VS7ZnlEK7eELFfc2EwNcRps7A-hbkvoN3XlQ=="
ORG = "GrowGuard"
URL = "http://192.168.2.140:8086"
BUCKET = "growguard"
INFLUXDB_CLIENT = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
DASHBOARD_URL = "http://192.168.2.140:8086/orgs/bcd6cfd2cb5b7d92/dashboards/0ccafde577c80000?lower=now%28%29+-+1h"



if __name__ == "__main__":
    influxdb_client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)

    st.set_page_config(page_title="Grow Guard", page_icon="🌵")
    st.title("Dashboard")
    
    with st.container(border=True):
        st.link_button("InfluxDB Dashboard", DASHBOARD_URL)
