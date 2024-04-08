
#define SOIL_HUM_PIN 34
#define ADC_MAX_VALUE 4095

float soil_humidity; // in %

void setup() {
  Serial.begin(9600);
}

void loop() {
  float analog_value = analogRead(SOIL_HUM_PIN);
  soil_humidity = (1.0-(analog_value/ADC_MAX_VALUE))*100;
  Serial.print("Soil Humidity: ");
  Serial.print(soil_humidity);
  Serial.println(" %");
  Serial.println(analog_value);
  delay(1000);
}
