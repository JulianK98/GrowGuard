#define WATER_PUMP_PIN 17

int pump_state = LOW;

void setup() {
  Serial.begin(9600);
  pinMode(WATER_PUMP_PIN, OUTPUT);
}

void loop() {
    
    if (pump_state == LOW) {
      pump_state = HIGH;
    } else {
      pump_state = LOW;
    }
    
    digitalWrite(WATER_PUMP_PIN, pump_state);
    delay(10000);
}
