#include <WiFi.h>
#include <WiFiMulti.h>
#include <InfluxDbClient.h>
#include "DHT.h"
#define DEVICE "ESP32"

// WiFi settings
WiFiMulti wifiMulti;
const char* wifi_ssid =  "FRITZ!Powerline 540E";
const char* wifi_password = "29007651062585801210";
const char* wifi_ssid_2 =  "FRITZ!Box 7590 ME";
const char* wifi_password_2 = "16076165919985523842";


// InfluxDB settings
#define INFLUXDB_URL "http://192.168.2.140:8086"
#define INFLUXDB_TOKEN "KDq3XStui1lHMXVc44jrWxPNebKXwcd1GiqiGsZ4S3W8QGcN6eGRR4a9S_4V7_ZloPnLwq54nTXxZsJ5RGto4Q=="
#define INFLUXDB_ORG "bcd6cfd2cb5b7d92"
#define INFLUXDB_BUCKET "growguard"
#define TZ_INFO "UTC2"
InfluxDBClient client(INFLUXDB_URL, INFLUXDB_ORG, INFLUXDB_BUCKET, INFLUXDB_TOKEN);

// Water pump settings
#define WATER_PUMP_PIN 17

// Temperature sensor settings
#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// Soil humidity sensor settings
#define SOIL_HUM_PIN 34
#define ADC_MAX_VALUE 4095

// Intervall settings
unsigned long previous_irrigation_ts = 0;
unsigned long previous_sensor_ts = 0;
unsigned long irrigation_intervall = 1000;
unsigned long sensor_intervall = 10000;

// Declare functions
bool get_start_irrigation_flag();
int get_pulse_length();
void set_start_irrigation_flag();
void report_irrigation(int pl);
void write_rssi();
void write_sensor_values(float temp, float air_hum, float soil_hum);


void setup() {
  Serial.begin(9600);

  // Setup temp sensor
  dht.begin();

  // Setup water pump
  pinMode(WATER_PUMP_PIN, OUTPUT);
  
  // Setup wifi
  WiFi.mode(WIFI_STA);
  wifiMulti.addAP(wifi_ssid, wifi_password);
  wifiMulti.addAP(wifi_ssid_2, wifi_password_2);
  Serial.print("Connecting to wifi");
  while (wifiMulti.run() != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  timeSync(TZ_INFO, "pool.ntp.org", "time.nis.gov");

  // Check server connection
  if (client.validateConnection()) {
    Serial.print("Connected to InfluxDB: ");
    Serial.println(client.getServerUrl());
  } else {
    Serial.print("InfluxDB connection failed: ");
    Serial.println(client.getLastErrorMessage());
  }

}

void loop() {
  unsigned long current_ts = millis();

  if (current_ts - previous_sensor_ts >= sensor_intervall) {
    previous_sensor_ts = current_ts;

    // Report WiFi signal strength
    write_rssi();

    // Measure temperature, air humidity and soil humidity
    float air_humidity = dht.readHumidity(); // in %
    float temperature = dht.readTemperature(); // in °C
    float sh_analog_value = analogRead(SOIL_HUM_PIN);
    float soil_humidity = (1.0-(sh_analog_value/ADC_MAX_VALUE))*100; // in %
    if (!isnan(temperature) && !isnan(air_humidity) && !isnan(soil_humidity)) {
      write_sensor_values(temperature, air_humidity, soil_humidity);
    } else {
      Serial.println(F("Failed to read sensor values!"));
    }
  }

  // Irrigation
  if (current_ts - previous_irrigation_ts >= irrigation_intervall) {
    previous_irrigation_ts = current_ts;

    if (get_start_irrigation_flag()) {
      int pulse_length = get_pulse_length();
      set_start_irrigation_flag();

      // Control water pump
      digitalWrite(WATER_PUMP_PIN, HIGH); 
      delay(pulse_length*1000);
      digitalWrite(WATER_PUMP_PIN, LOW);

      report_irrigation(pulse_length); 
    }
  }


  // Check WiFi connection and reconnect if needed
  if (wifiMulti.run() != WL_CONNECTED) {
    Serial.println("Wifi connection lost");
  }

  delay(10);
}


bool get_start_irrigation_flag() {
  String query = "from(bucket: \"growguard\") \
    |> range(start: -100000h) \
    |> filter(fn: (r) => r._measurement == \"irrigation\") \
    |> filter(fn: (r) => r._field == \"start-irrigation\") \
    |> last()";

  FluxQueryResult result = client.query(query);
  
  result.next();
  bool si_flag = result.getValueByName("_value").getBool();

  if (result.getError() != "") {
    Serial.print("Query result error: ");
    Serial.println(result.getError());
  }
  result.close();

  return si_flag;
}

int get_pulse_length() {
  String query = "from(bucket: \"growguard\") \
    |> range(start: -100000h) \
    |> filter(fn: (r) => r._measurement == \"irrigation\") \
    |> filter(fn: (r) => r._field == \"pulse-length\") \
    |> last()";

  FluxQueryResult result = client.query(query);

  result.next();
  int pl = result.getValueByName("_value").getLong();

  if (result.getError() != "") {
    Serial.print("Query result error: ");
    Serial.println(result.getError());
  }
  result.close();

  return pl;
}

void set_start_irrigation_flag() {
  Point point_si("irrigation");
  
  point_si.addField("start-irrigation", false);
  
  if (!client.writePoint(point_si)) {
    Serial.print("InfluxDB write failed: ");
    Serial.println(client.getLastErrorMessage());
  }
}

void report_irrigation(int pl) {
  Point point_id("irrigation");
  
  point_id.addField("irrigation-done", pl);
  
  if (!client.writePoint(point_id)) {
    Serial.print("InfluxDB write failed: ");
    Serial.println(client.getLastErrorMessage());
  }
}

void write_rssi() {
  Point point_wifi("wifi_status");
  
  point_wifi.addTag("device", DEVICE);
  point_wifi.addTag("SSID", WiFi.SSID());
  point_wifi.addField("rssi", WiFi.RSSI());
  
  if (!client.writePoint(point_wifi)) {
    Serial.print("InfluxDB write failed: ");
    Serial.println(client.getLastErrorMessage());
  }
}

void write_sensor_values(float temp, float air_hum, float soil_hum) {
  Point point_sensor("sensors");
  
  point_sensor.addField("temperature", temp);
  point_sensor.addField("air-humidity", air_hum);
  point_sensor.addField("soil-humidity", soil_hum);
  
  if (!client.writePoint(point_sensor)) {
    Serial.print("InfluxDB write failed: ");
    Serial.println(client.getLastErrorMessage());
  }
}






