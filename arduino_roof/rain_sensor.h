#include <Arduino.h>

// Initializes the rain sensor.
void initialize_rain();

class RainAmountMeasurement {
 public:
  // Initializes rain amount measurement.
  // Can be used repeatedly, will re-start measurements.
  void start();

  // Finishes wind speed measurement.
  // start_recording() must be called first.
  // Returns the amount of rain that has fallen
  // since start_recording, in mm.
  float rain_amount();

 private:
  uint32_t initial_interrupts;
};
