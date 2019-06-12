#include <Arduino.h>

// Initializes the wind sensors.
void initialize_wind();

class WindSpeedMeasurement {
 public:
  // Initializes wind speed measurement.
  // Can be used repeatedly, will re-start measurements.
  void start();

  // Finishes wind speed measurement.
  // start_recording() must be called first.
  // Returns the average wind speed in meters / second
  // since the last start_recording() call.
  float average_wind_speed();

 private:
  uint32_t initial_interrupts;
  unsigned long initial_millis;
};

// Raw reading from the wind direction input.
uint32_t get_raw_wind_direction();
