/*

An Arduino controller for the weather station, at the
ground level. Output is shown on the LCD screen and
written to the serial port with SERIAL_BAUD speed,
in the following form:
  - "Temperature: XX.X\n"
  - "Pressure: XXXX.X\n"

Units:
  - Humidity: percentage (relative humidity)
  - Temperature: degrees Celsius
  - Water level: raw analog pin reading
  - Pressure: hPa
  - PM 1.0, PM 2.5, PM 10.0: ug/m3

Pin layout (for Arduino Nano):
  - A0: water level sensor analog output
  - D7: DHT11 humidity & temperature input/output pin
  - A4: SDA pin for LCD and pressure sensor
  - A5: SCL ping for LCD and pressure sensor
  - D4: PMS5003 serial output (PIN5 in the datasheet)
  - D5: no connect

Connecting LCD is optional.

Required libraries:
  - Adafruit Unified Sensor, ver >= 1.0.3
  - DHT sensor library, ver >= 1.3.4
  - Adafruit BMP085 library >= 1.0.0

*/

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>
#include <Adafruit_BMP085.h>
#include <SoftwareSerial.h>

#include "pms5003.h"

// Output is written to serial.
#define SERIAL_BAUD 9600

// Temperature and humidity sensor.
#define DHTPIN 7
#define DHTTYPE AM2301
DHT dht(DHTPIN, DHTTYPE);

// Water level sensor.
#define WATER_SENSOR A0
#define WATER_ENABLED false

// Pressure sensor.
Adafruit_BMP085 bmp;

// Air quality sensor (PMS).
#define PMS_DATA_INPUT 4
#define UNUSED_PMS_DATA_OUTPUT 5
SoftwareSerial pmsSerial(PMS_DATA_INPUT, UNUSED_PMS_DATA_OUTPUT);

// Set the LCD address to 0x27 for a 16 chars and 2 line display.
LiquidCrystal_I2C lcd(0x27, 20, 4);

void setup() {
  // Initializes the output seral port.
  Serial.begin(SERIAL_BAUD);
  while (!Serial);

  // Initializes LCD.
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Starting");

  // Initializes DHT (temp & humidity) sensor.
  dht.begin();

  // Initializes pressure sensor.
  bmp.begin();

  // Initializes the PMS serial port.
  pmsSerial.begin(9600);

  // Wait a few seconds at start, so that sensorts settle.
  delay(5000);
}

// For the LCD.
//   0: humidity and temperature
//   1: water level
int display_page = 0;

void loop() {
  // At the beginning we busy wait for a while
  // for the PMS unit to start sending data.
  // Note that we may miss the reading if the transmission
  // doesn't start before the loop terminates.
  struct pms5003data pms_data;
  bool pms_data_available = false;
  for (int i = 0; i < 5000; ++i) {
    if(readPMSdata(&pmsSerial, &pms_data)) {
      pms_data_available = true;
    }
  }

  // Print air quality data.
  if (pms_data_available) {
    Serial.print("PM 1.0 standard: ");
    Serial.println(pms_data.pm10_standard);
    Serial.print("PM 2.5 standard: ");
    Serial.println(pms_data.pm25_standard);
    Serial.print("PM 10.0 standard: ");
    Serial.println(pms_data.pm100_standard);

    Serial.print("PM 1.0 environmental: ");
    Serial.println(pms_data.pm10_env);
    Serial.print("PM 2.5 environmental: ");
    Serial.println(pms_data.pm25_env);
    Serial.print("PM 10.0 environmental: ");
    Serial.println(pms_data.pm100_env);

    Serial.print("Particles > 0.3um / 0.1L air: ");
    Serial.println(pms_data.particles_03um);
    Serial.print("Particles > 0.5um / 0.1L air: ");
    Serial.println(pms_data.particles_05um);
    Serial.print("Particles > 1.0um / 0.1L air: ");
    Serial.println(pms_data.particles_10um);
    Serial.print("Particles > 2.5um / 0.1L air: ");
    Serial.println(pms_data.particles_25um);
    Serial.print("Particles > 5.0um / 0.1L air: ");
    Serial.println(pms_data.particles_50um);
    Serial.print("Particles > 10.0 um / 0.1L air: ");
    Serial.println(pms_data.particles_100um);
  }

  // Read temperature and humidity.
  const float h = dht.readHumidity();
  const float t = dht.readTemperature();

  // Print temperature and humidity.
  if (!isnan(h)) {
    Serial.print("Humidity: ");
    Serial.println(h);
  }
  if (!isnan(t)) {
    Serial.print("Temperature: ");
    Serial.println(t);
  }

  // Read and print water level.
  int water = 0;
  if (WATER_ENABLED) {
    water = analogRead(WATER_SENSOR);
    Serial.print("Water level: ");
    Serial.println(water);
  }

  // Read and print pressure.
  const float pressure = bmp.readPressure() / 100.0;
  Serial.print("Pressure: ");
  Serial.println(pressure);

  // Print data to LCD.
  lcd.clear();
  if (display_page == 0) {
    // Print a message to the LCD.
    lcd.setCursor(0, 0);
    lcd.print("Hmdt: ");
    lcd.print(h);
    lcd.print(" %");

    lcd.setCursor(0, 1);
    lcd.print("Temp: ");
    lcd.print(t);
    lcd.print(" C");
  }
  if (display_page == 1) {
    if (WATER_ENABLED) {
      lcd.setCursor(0, 0);
      lcd.print("Water: ");
      lcd.print(water);
    }

    lcd.setCursor(0, 1);
    lcd.print("Pres: ");
    lcd.print(pressure);
    lcd.print("hPa");
  }

  display_page = display_page + 1;
  if (display_page == 2) {
    display_page = 0;
  }

  // Wait a while before measuring again.
  delay(2000);
}
