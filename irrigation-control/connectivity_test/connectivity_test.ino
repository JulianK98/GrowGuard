#include <WiFi.h>
#include <WiFiMulti.h>
#include <InfluxDbClient.h>
#define DEVICE "ESP32"

// WiFi settings
WiFiMulti wifiMulti;
const char* wifi_ssid =  "FRITZ!Powerline 540E";
const char* wifi_password = "29007651062585801210";

// InfluxDB settings
#define INFLUXDB_URL "http://192.168.2.140:8086"
#define INFLUXDB_TOKEN "KDq3XStui1lHMXVc44jrWxPNebKXwcd1GiqiGsZ4S3W8QGcN6eGRR4a9S_4V7_ZloPnLwq54nTXxZsJ5RGto4Q=="
#define INFLUXDB_ORG "bcd6cfd2cb5b7d92"
#define INFLUXDB_BUCKET "growguard"
#define TZ_INFO "UTC2"

InfluxDBClient client(INFLUXDB_URL, INFLUXDB_ORG, INFLUXDB_BUCKET, INFLUXDB_TOKEN);

// Declare Data points
Point sensor("wifi_status");

void setup()
{
    Serial.begin(9600);
    
    // Setup wifi
    WiFi.mode(WIFI_STA);
    wifiMulti.addAP(wifi_ssid, wifi_password);
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

    sensor.addTag("device", DEVICE);
    sensor.addTag("SSID", WiFi.SSID());
}

void loop() {
  sensor.clearFields();

  // Report RSSI of currently connected network
  sensor.addField("rssi", WiFi.RSSI());

  // Print what are we exactly writing
  //Serial.print("Writing: ");
  //Serial.println(sensor.toLineProtocol());

  // Write point
  if (!client.writePoint(sensor)) {
    Serial.print("InfluxDB write failed: ");
    Serial.println(client.getLastErrorMessage());
  }

  String query = "from(bucket: \"growguard\")\
  |> range(start: -10000h)\
  |> filter(fn: (r) => r._measurement == \"home\")\
  |> filter(fn: (r) => r._field == \"soil-humidity\")\
  |> last()";

  // Print composed query
    Serial.println("Querying for RSSI values written to the \"sample-bucket\" bucket in the last 1 min... ");
    Serial.println(query);
  
    // Send query to the server and get result
    FluxQueryResult result = client.query(query);
  
    Serial.println("Results : ");
    // Iterate over rows.
    while (result.next()) {   
      Serial.print("Soil Humidity: ");
      // Get value of column named '_value'
      long value = result.getValueByName("_value").getLong();
      Serial.print(value);
  
      // Get value for the _time column
      FluxDateTime time = result.getValueByName("_time").getDateTime();
  
      String timeStr = time.format("%F %T");
  
      Serial.print(" at ");
      Serial.print(timeStr);
  
      Serial.println();
    }
  
    // Report any error
    if (result.getError() != "") {
      Serial.print("Query result error: ");
      Serial.println(result.getError());
    }
  
    // Close the result
    result.close();
  
    Serial.println("==========");

  // Check WiFi connection and reconnect if needed
  if (wifiMulti.run() != WL_CONNECTED) {
    Serial.println("Wifi connection lost");
  }

  Serial.println("Waiting 5 second");
  delay(5000);
}

