#include "rain_sensor.h"

// Rain gauge connection
#define RAIN_PIN 3

// Number of quiet microsecons required to register a new
// interrupt (debounce).
#define INTERRUPT_DEBOUNCE_US 5000


// Last time a rain interrupt was called.
// Used to debounce the interrupts (i.e. ignore
// interrupts for a moment after one happens).
static volatile unsigned long last_time_rain = 0;

// Number of rain interrupts.
static volatile uint32_t rain_interrupts = 0;

// Interrupt handler for the rain gauge.
static void rain_interrupt_handler() {
  const unsigned long time_since_last = micros() - last_time_rain;
  last_time_rain = micros();

  if (time_since_last > INTERRUPT_DEBOUNCE_US) {
    rain_interrupts++;
  }
}

void initialize_rain() {
  // Set up the rain gauge pin.
  pinMode(RAIN_PIN, INPUT_PULLUP);

  // Wait a while for the values to settle.
  delay(200);

  // Attach the rain interrupt handler.
  attachInterrupt(
    digitalPinToInterrupt(RAIN_PIN),
    rain_interrupt_handler,
    RISING);

  // Wait a little more and clear the interrupt counts.
  // For unknown reason there are spurious interrupts
  // around startup.
  delay(200);
  noInterrupts();
  rain_interrupts = 0;
  interrupts();
}

uint32_t get_rain_interrupt_count() {
  noInterrupts();
  volatile uint32_t rain_copy = rain_interrupts;
  interrupts();
  return rain_copy;
}
