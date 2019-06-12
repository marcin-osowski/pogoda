#include "wind_sensors.h"

// Anemometer connection
#define ANEMO_PIN 2

// Wind direction connection
#define WIND_DIRECTION_PIN A4

// Number of quiet microsecons required to register a new
// interrupt (debounce).
#define INTERRUPT_DEBOUNCE_US 5000


// Last time an anemo interrupt was called.
// Used to debounce the interrupts (i.e. ignore
// interrupts for a moment after one happens).
static volatile unsigned long last_time_anemo = 0;

// Number of anemo interrupts.
static volatile uint32_t anemo_interrupts = 0;

// Interrupt handler for the anemometer.
static void anemo_interrupt_handler() {
  const unsigned long time_since_last = micros() - last_time_anemo;
  last_time_anemo = micros();

  if (time_since_last > INTERRUPT_DEBOUNCE_US) {
    anemo_interrupts++;
  }
}

void initialize_wind() {
  // Set up the anemometer pin.
  pinMode(ANEMO_PIN, INPUT_PULLUP);

  // Wait a while for the values to settle.
  delay(200);

  // Attach the interrupt handler.
  attachInterrupt(
    digitalPinToInterrupt(ANEMO_PIN),
    anemo_interrupt_handler,
    RISING);

  // Wait a little more and clear the interrupt count.
  // For unknown reason(s) there are spurious interrupts
  // around startup.
  delay(200);
  noInterrupts();
  anemo_interrupts = 0;
  interrupts();
}

uint32_t get_anemo_interrupt_count() {
  noInterrupts();
  volatile uint32_t anemo_copy = anemo_interrupts;
  interrupts();
  return anemo_copy;
}

uint32_t get_raw_wind_direction() {
  return analogRead(WIND_DIRECTION_PIN);
}
