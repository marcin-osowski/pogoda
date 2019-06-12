/*

An Arduino controller for the weather station, installed
at the roof. Output is written to the serial port with
SERIAL_BAUD speed, in the following form:
  - Wind speed: 3.10
  - Wind direction: 90.00
  - Wind direction text: east
  - Rain since last output: 0.20

Units:
  - Wind speed: m/s
  - Wind direction: degrees from north (e.g., 90 = east)
  - Wind direction text: text
  - Rain since last output: milimeters of rain


Pin layout (for Arduino Nano):
  - D2: anemometer. Other wire from the anemometer should
        be connected to the ground.
  - D3: rain gauge. Other wire from the rain gauge should
        be connected to the ground.
  - A4: wind direction sensor. A4 should be connected via a
        10k resistor to 3.3 volts. The other wire from the wind
        direction sensor should be connected to the ground.

*/

#include "wind_sensors.h"
#include "rain_sensor.h"

// Output is written to serial.
#define SERIAL_BAUD 9600

// Delay between successive reads (ms).
#define READ_DELAY_MS (30 * 1000)


void setup() {
  // Initialize the output seral port.
  Serial.begin(SERIAL_BAUD);
  while (!Serial);

  // Initialize wind and rain sensors.
  initialize_wind();
  initialize_rain();

  // Welcome message.
  Serial.println("Wind and rain sensor");
  Serial.println("Wind speed unit: meters/second");
  Serial.println("Wind direction unit: degrees (and text)");
  Serial.println("Rain unit: milimeters");
  Serial.print("Output every ");
  Serial.print(READ_DELAY_MS / 1000.0);
  Serial.println(" seconds.");
  Serial.println("Waiting for first measurement");
}

void loop() {
  // Start measurements.
  WindSpeedMeasurement wind;
  wind.start();
  RainAmountMeasurement rain;
  rain.start();

  // Wait for a while.
  delay(READ_DELAY_MS);

  // Output data.
  Serial.print("Wind speed: ");
  Serial.println(wind.average_wind_speed());

  Serial.print("Wind direction: ");
  Serial.println(get_wind_direction());

  Serial.print("Wind direction text: ");
  Serial.println(get_wind_direction_text());

  Serial.print("Rain since last output: ");
  Serial.println(rain.rain_amount());
}
