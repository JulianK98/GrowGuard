from datetime import datetime, timedelta
from time import sleep
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS



class DBCom:
    
    def __init__(self, url: str, token: str, org: str, bucket: str) -> None:
        self.influxdb_client = InfluxDBClient(url=url, token=token, org=org)
        self.org = org
        self.bucket = bucket

    def load_sensors_data(self) -> dict:
        query_api = self.influxdb_client.query_api()

        query = f"""
        from(bucket: "{self.bucket}")
        |> range(start: -1h)
        |> filter(fn: (r) => r._measurement == "sensors")
        |> last()
        """

        tables = query_api.query(query, org=self.org)

        if tables != []:
            latest_values = {"time": tables[0].records[0].get_time()}
            for table in tables:
                for record in table.records:
                    latest_values.update({record.get_field(): record.get_value()})
        else:
            latest_values = {
                "time": "--",
                "temperature": "-- ",
                "air-humidity": "-- ",
                "air-pressure": "-- ",
                "soil-humidity": "-- ",
            }

        return latest_values


    def get_irrigation_count(self) -> int:
        query_api = self.influxdb_client.query_api()

        query = f"""
        from(bucket: "{self.bucket}")
        |> range(start: today())
        |> filter(fn: (r) => r._measurement == "irrigation")
        |> filter(fn: (r) => r._field == "irrigation-done")
        |> count()
        """

        tables = query_api.query(query, org=self.org)

        if tables != []:
            count = tables[0].records[0].get_value()
        else:
            count = 0

        return count


    def get_last_irrigation_time(self) -> datetime | None:
        query_api = self.influxdb_client.query_api()

        query = f"""
        from(bucket: "{self.bucket}")
        |> range(start: today())
        |> filter(fn: (r) => r._measurement == "irrigation")
        |> filter(fn: (r) => r._field == "irrigation-done")
        |> last()
        """

        tables = query_api.query(query, org=self.org)

        if tables != []:
            time = tables[0].records[0].get_time()
        else:
            time = None

        return time


    def get_irrigation_time_today(self) -> int:
        query_api = self.influxdb_client.query_api()

        query = f"""
        from(bucket: "{self.bucket}")
        |> range(start: today())
        |> filter(fn: (r) => r._measurement == "irrigation")
        |> filter(fn: (r) => r._field == "irrigation-done")
        |> sum()
        """

        tables = query_api.query(query, org=self.org)

        if tables != []:
            irr_time = tables[0].records[0].get_value()
        else:
            irr_time = 0

        return irr_time


    def load_settings_data(self) -> dict:
        query_api = self.influxdb_client.query_api()

        query = f"""
        from(bucket: "{self.bucket}")
        |> range(start: -100000h)
        |> filter(fn: (r) => r._measurement == "settings")
        |> last()
        """

        tables = query_api.query(query, org=self.org)

        settings_values = {"time": tables[0].records[0].get_time()}
        for table in tables:
            for record in table.records:
                settings_values.update({record.get_field(): record.get_value()})

        return settings_values


    def get_pulse_length(self) -> int:
        query_api = self.influxdb_client.query_api()

        query = f"""
        from(bucket: "{self.bucket}")
        |> range(start: -100000h)
        |> filter(fn: (r) => r._measurement == "irrigation")
        |> filter(fn: (r) => r._field == "pulse-length")
        |> last()
        """

        tables = query_api.query(query, org=self.org)

        if tables != []:
            pulse_length = tables[0].records[0].get_value()
        else:
            pulse_length = 0

        return pulse_length

    def get_auto_mode_settings(self) -> dict:
        query_api = self.influxdb_client.query_api()

        query = f"""
        from(bucket: "{self.bucket}")
        |> range(start: -1000000h)
        |> filter(fn: (r) => r._measurement == "settings")
        |> filter(fn: (r) => r._field == "last-irr-limit" or r._field == "pulse-length" or r._field == "soil-hum-limit")
        |> last()
        """

        tables = query_api.query(query, org=self.org)

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


    def write_settings_data(self, param: str, value) -> None:
        write_api = self.influxdb_client.write_api(write_options=SYNCHRONOUS)

        point = Point("settings").field(param, value)

        write_api.write(bucket=self.bucket, org=self.org, record=point)


    def send_irrigation_signal(self) -> None:
        write_api = self.influxdb_client.write_api(write_options=SYNCHRONOUS)

        point = Point("irrigation").field("start-irrigation", True)

        write_api.write(bucket=self.bucket, org=self.org, record=point)


    def write_pulse_length(self, pulse_length: int) -> None:
        write_api = self.influxdb_client.write_api(write_options=SYNCHRONOUS)

        point = Point("irrigation").field("pulse-length", pulse_length)

        write_api.write(bucket=self.bucket, org=self.org, record=point)


    def update_auto_mode_settings(self, last_irr_limit: float, soil_hum_limit: int, pulse_length: int) -> None:
        write_api = self.influxdb_client.write_api(write_options=SYNCHRONOUS)

        point = Point("settings")
        point.field("last-irr-limit", last_irr_limit)
        point.field("soil-hum-limit", soil_hum_limit)
        point.field("pulse-length", pulse_length)

        write_api.write(bucket=self.bucket, org=self.org, record=point)

if __name__ == "__main__":

    TOKEN = "ONRceIkyGlQs6jSymPUaFQT8yvViUtxCINTv9cHrrb7fdUP0FjJMbz5Tb3O4kl9NT06VjiS2zImcM0-5bevxGg=="
    ORG = "GrowGuard"
    URL = "http://192.168.2.140:8086"
    # URL = "http://192.168.2.201:8086"
    BUCKET = "growguard"
    DASHBOARD_URL = "http://192.168.2.140:8086/orgs/bcd6cfd2cb5b7d92/dashboards/0ccafde577c80000?lower=now%28%29+-+1h"
    # DASHBOARD_URL = "http://192.168.2.201:8086/orgs/199d6cf6fc399db4/dashboards/0cdc691f04fbc000?lower=now%28%29+-+1h"
    
    db_com = DBCom(URL, TOKEN, ORG, BUCKET)
    settings = db_com.get_auto_mode_settings()
    print(settings)
    