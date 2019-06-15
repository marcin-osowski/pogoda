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

// Number of wind direction measurements per read.
#define WIND_DIRECTION_TIMES_PER_READ 100


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
  // Start wind speed measurement.
  WindSpeedMeasurement wind_speed;
  wind_speed.start();

  // Start wind direction measurement.
  WindDirectionMeasurement wind_direction;

  // Take WIND_DIRECTION_TIMES_PER_READ measurements.
  for (int i = 0; i < WIND_DIRECTION_TIMES_PER_READ; ++i) {
    wind_direction.next_measurement();
    delay(READ_DELAY_MS / WIND_DIRECTION_TIMES_PER_READ);
  }

  const uint8_t wind_direction_idx =
    wind_direction.most_common_direction();

  // Output data.
  Serial.print("Wind speed: ");
  Serial.println(wind_speed.average_wind_speed());

  if (wind_direction_idx == 255) {
    Serial.println("No valid wind direction measurement.");
  } else {
    Serial.print("Wind direction: ");
    Serial.println(wind_direction_to_degrees(wind_direction_idx));

    Serial.print("Wind direction text: ");
    Serial.println(wind_direction_to_text(wind_direction_idx));
  }

  Serial.print("Total rain: ");
  Serial.println(total_rain_mm());
}
