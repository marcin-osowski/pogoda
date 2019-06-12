#include <Arduino.h>

// Initializes the wind sensors.
void initialize_wind();

// A function that correctly reads the
// current amount of anemo interrupts.
uint32_t get_anemo_interrupt_count();

// Raw reading from the wind direction input.
uint32_t get_raw_wind_direction();
