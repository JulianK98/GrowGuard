import os
import sys
import streamlit as st
from datetime import datetime, timedelta
from time import sleep
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from db_communication import DBCom

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

DB_COM = DBCom(URL, TOKEN, ORG, BUCKET)


# Irrigation process data
PUMP_POWER = 9.5  # ml/s


def measurement_intervall_change():
    DB_COM.write_settings_data("measurement-intervall", st.session_state.meas)


def auto_irrigation_change():
    DB_COM.write_settings_data("auto-irrigation", st.session_state.auto)


def on_man_irr_click():
    DB_COM.send_irrigation_signal()


def pulse_length_change():
    DB_COM.write_pulse_length(st.session_state.pl)


def main():
    # General settings
    st.set_page_config(page_title="Grow Guard", page_icon="🌵")
    st.title("Grow Guard - Smart Irrigation")

    if DEV:
        st.header("Dev Mode - using local InfluxDB instance")
    
    # Load data from InfluxDB
    latest_data = DB_COM.load_sensors_data()
    settings_data = DB_COM.load_settings_data()
    irrigation_count = DB_COM.get_irrigation_count()
    last_irrigation_time = DB_COM.get_last_irrigation_time()
    water_consumption_today = DB_COM.get_irrigation_time_today() * PUMP_POWER
    prev_pulse_length = DB_COM.get_pulse_length()
    auto_mode_settings = DB_COM.get_auto_mode_settings()

    # Irrigation container
    with st.container(border=True):
        st.subheader("Irrigation")

        with st.container(border=True):
            auto_irrigation = st.toggle(
                "Automatic Irrigation",
                settings_data["auto-irrigation"],
                key="auto",
                on_change=auto_irrigation_change,
            )

        with st.container(border=True):
            col1, col2 = st.columns(2)
            manual_irrigation = col1.button(
                "Manual Irrigation",
                type="primary",
                key="man_irr",
                disabled=auto_irrigation,
                on_click=on_man_irr_click,
            )

            pulse_length = col2.slider(
                "Pulse Length [s]:",
                1,
                20,
                prev_pulse_length,
                key="pl",
                disabled=auto_irrigation,
                on_change=pulse_length_change,
            )

        col1, col2, col3 = st.columns(3)
        if last_irrigation_time != None:
            last_irrigation_time_str = (last_irrigation_time + timedelta(hours=2)).strftime("%H:%M")
        else:
            last_irrigation_time_str = "--:--"
        last_irrigation = col1.metric("Last Irrigation", last_irrigation_time_str)

        irrigation_count = col2.metric("Irrigations Today", irrigation_count)

        water_consumption = col3.metric(
            "Water Consumption Today", f"{water_consumption_today} ml"
        )

    # Mini dashboard container
    with st.container(border=True):
        st.subheader("Sensors")

        # meas_interval_options = [1, 5, 10, 30]
        # measurement_intervall = st.selectbox(
        #     "Measurement Intervall [s]",
        #     meas_interval_options,
        #     index=meas_interval_options.index(settings_data["measurement-intervall"]),
        #     key="meas",
        #     on_change=measurement_intervall_change,
        # )

        col1, col2 = st.columns(2)

        temp_value = latest_data["temperature"]
        temp_metric = col1.metric("Temperature", f"{temp_value}°C")

        air_hum_value = latest_data["air-humidity"]
        air_hum_metric = col2.metric("Air Humidity", f"{air_hum_value}%")

        # air_pressure_value = latest_data["air-pressure"]
        air_pressure_value = "-- "
        air_pressure_metric = col1.metric("Air Pressure", f"{air_pressure_value}bar")

        soil_hum_value = latest_data["soil-humidity"]
        soil_hum_metric = col2.metric("Soil Humidity", f"{soil_hum_value}%")

    # Irrigation - Auto Mode settings
    with st.form(key='auto_mode_settings'):
        st.subheader("Irrigation - Auto Mode Settings")
        
        col1, col2 = st.columns(2)
        
        pulse_length_auto = col1.slider(
            "Pulse Length [s]:",
            1,
            20,
            auto_mode_settings["pulse-length"]
        )
        last_irr_limit = col1.slider(
            "Last Irrigation Limit [h]:",
            0.25,
            10.0,
            auto_mode_settings["last-irr-limit"],
            step=0.25
        )
        soil_hum_limit = col2.slider(
            "Soil Humidity Limit [%]:",
            0,
            100,
            auto_mode_settings["soil-hum-limit"]
        )
        
        submit = col1.form_submit_button(label='Update Settings')
        
        if submit:
            DB_COM.update_auto_mode_settings(last_irr_limit, soil_hum_limit, pulse_length_auto)    


if __name__ == "__main__":
    main()
    