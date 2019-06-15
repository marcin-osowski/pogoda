#include <Arduino.h>

// Initializes the wind sensors.
void initialize_wind();

// Access class for wind speed. Computes the average wind
// speed between the start() and average_wind_speed() calls.
// More than one instance can be start()ed at the same time.
class WindSpeedMeasurement {
 public:
  // Initializes wind speed measurement.
  // Can be used repeatedly, will re-start measurements.
  void start();

  // Returns the average wind speed in meters / second
  // since the last start() call.
  // start() must be called first.
  float average_wind_speed() const;

 private:
  uint32_t initial_interrupts;
  unsigned long initial_millis;
};

// Internally wind directions are represented by
// an index between 0 and NUM_WIND_DIRECTIONS - 1.
#define NUM_WIND_DIRECTIONS 16

// Reads the current wind direction analog input
// and returns the wind direction index.
// Returned index is between 0 and XX.
// Returns 255 on read error.
uint8_t get_wind_direction_now();

// Converts the wind direction index to degrees.
// Returns -1.0 if the direction index is invalid.
// Returns the degrees from north, so 0.0
// for north, 90.0 for east, 45.0 for north-east or
// 22.5 for north - north-east.
float wind_direction_to_degrees(uint8_t direction_idx);

// Converts the wind direction to null terminated strings).
// Returns a pointer to "error" if the direction index is invalid.
const char* wind_direction_to_text(uint8_t direction_idx);

// A class that repeatedly takes wind direction measurements
// and returns the most commonly measured wind direction.
// This helps to denoise the input from the wind vane
// which normally fluctuates left and right.
//
// Usage pattern: call next_measurement() several times with
// time delay between calls, and then most_common_direction()
// to get the index of the most common direction.
class WindDirectionMeasurement {
 public:
  WindDirectionMeasurement();

  // Gets one wind direction measurement
  // and saves the result.
  void next_measurement();

  // Returns the most common wind direction obtained
  // via next_measurement() calls.
  // Returns 255 if there's no such direction (for example
  // if next_measurement() was never called or all measurements
  // resulted in an error).
  uint8_t most_common_direction() const;

 private:
  uint16_t directions_count[NUM_WIND_DIRECTIONS];
};
