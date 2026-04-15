/*
 * Smart Farm Arduino Sensor System
 * 
 * Hardware:
 * - Arduino Uno/Nano
 * - DHT22 Temperature & Humidity Sensor
 * - Soil Moisture Sensor (Analog)
 * 
 * Connections:
 * DHT22:
 *   - VCC → 5V
 *   - GND → GND
 *   - DATA → Pin 2
 * 
 * Soil Moisture Sensor:
 *   - VCC → 5V
 *   - GND → GND
 *   - A0 → Analog Pin A0
 */

#include <DHT.h>

// Pin Definitions
#define DHTPIN 2          // DHT22 data pin
#define DHTTYPE DHT22     // DHT sensor type
#define SOIL_PIN A0       // Soil moisture sensor analog pin

// Initialize DHT sensor
DHT dht(DHTPIN, DHTTYPE);

// Calibration values for soil moisture sensor
// Adjust these based on your sensor!
const int AIR_VALUE = 620;    // Sensor value in air (dry)
const int WATER_VALUE = 310;  // Sensor value in water (wet)

void setup() {
  // Start serial communication
  Serial.begin(9600);
  
  // Initialize DHT sensor
  dht.begin();
  
  // Wait for sensor to stabilize
  delay(2000);
  
  Serial.println("Smart Farm Sensor System Ready!");
}

void loop() {
  // Read DHT22 sensor
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  
  // Read soil moisture sensor
  int soilRaw = analogRead(SOIL_PIN);
  
  // Convert to percentage (0% = dry, 100% = wet)
  float soilMoisture = map(soilRaw, AIR_VALUE, WATER_VALUE, 0, 100);
  soilMoisture = constrain(soilMoisture, 0, 100);
  
  // Check if DHT reading failed
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("{\"error\": \"DHT sensor read failed\"}");
    delay(5000);
    return;
  }
  
  // Send data as JSON
  Serial.print("{\"temp\": ");
  Serial.print(temperature, 1);
  Serial.print(", \"humidity\": ");
  Serial.print(humidity, 1);
  Serial.print(", \"soil_moisture\": ");
  Serial.print(soilMoisture, 1);
  Serial.println("}");
  
  // Wait 5 seconds before next reading
  delay(5000);
}
