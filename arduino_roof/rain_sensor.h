#include <Arduino.h>

// Initializes the rain sensor.
void initialize_rain();

// A function that correctly reads the
// current amount of rain interrupts.
uint32_t get_rain_interrupt_count();
