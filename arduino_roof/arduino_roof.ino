/*

An Arduino controller for the weather station, installed
at the roof. Output is ritten to the serial port with
SERIAL_BAUD speed, in the following form:
  - TODO

Units:
  - TODO

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


void setup() {
  // Initialize the output seral port.
  Serial.begin(SERIAL_BAUD);
  while (!Serial);

  // Initialize wind and rain sensors.
  initialize_wind();
  initialize_rain();
}

void loop() {
  WindSpeedMeasurement wind;
  wind.start();

  RainAmountMeasurement rain;
  rain.start();

  delay(1000);
  Serial.print("Rain [mm]: ");
  Serial.println(rain.rain_amount());
  Serial.print("Average wind speed [m/s]: ");
  Serial.println(wind.average_wind_speed());
  Serial.print("Direction: ");
  Serial.print(get_wind_direction_text());
  Serial.print(" (");
  Serial.print(get_wind_direction());
  Serial.println(" deg)");
}
