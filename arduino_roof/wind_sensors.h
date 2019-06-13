#include <Arduino.h>

// Initializes the wind sensors.
void initialize_wind();

// Access class, computes the average wind speed
// between start() and average_wind_speed() calls.
// More than one instance can be start()ed at the
// same time.
class WindSpeedMeasurement {
 public:
  // Initializes wind speed measurement.
  // Can be used repeatedly, will re-start measurements.
  void start();

  // Returns the average wind speed in meters / second
  // since the last start() call.
  // start() must be called first.
  float average_wind_speed();

 private:
  uint32_t initial_interrupts;
  unsigned long initial_millis;
};

// Read the wind direction input. Returns the degrees
// from north of the current direction speed (so 0.0
// for north, 90.0 for east, 45.0 for north-east or
// 22.5 for north - north-east). Returns -1.0 when
// reading fails.
float get_wind_direction();

// Same but with textual output (null terminated strings).
// Returns a pointer to "error" if reading fails.
const char* get_wind_direction_text();
