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

// A function that correctly reads the
// current amount of anemo interrupts.
static uint32_t get_anemo_interrupt_count() {
  noInterrupts();
  volatile uint32_t anemo_copy = anemo_interrupts;
  interrupts();
  return anemo_copy;
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

void WindSpeedMeasurement::start() {
  initial_interrupts = get_anemo_interrupt_count();
  initial_millis = millis();
}

float WindSpeedMeasurement::average_wind_speed() {
  const uint32_t now_interrupts = get_anemo_interrupt_count();
  const unsigned long now_millis = millis();

  // The interrupt is called once per second when
  // the speed of the wind is 1.492 miles/h
  // or 2.4 km/h or 0.666667 m/s.
  // Otherwise scales approximately linearly.

  const float interrupts_per_ms =
    ((float)(now_interrupts - initial_interrupts)) /
    ((float)(now_millis - initial_millis));

  const float speed_m_s = interrupts_per_ms * (1000.0f * 0.666667f);

  return speed_m_s;
}

static bool cmp_margin(const int value, const int reference) {
  const int delta = value - reference;
  return delta >= -10 && delta <= 10;
}

float get_wind_direction() {
  const int reading = analogRead(WIND_DIRECTION_PIN);

  // Note: the numeric constants were measured for the
  // particular setup: Arduino 3v3 voltage regulator,
  // the particular 10k ohm resistor, and the particular
  // wind vane unit.

  // Try the 8 major directions first.
  // Major directions are most commonly output by the
  // device.
  if (cmp_margin(reading, 539)) {
    // North.
    return 0.0f;
  }
  if (cmp_margin(reading, 318)) {
    // North-east.
    return 45.0f;
  }
  if (cmp_margin(reading, 63)) {
    // East.
    return 90.0f;
  }
  if (cmp_margin(reading, 127)) {
    // South-east.
    return 135.0f;
  }
  if (cmp_margin(reading, 197)) {
    // South.
    return 180.0f;
  }
  if (cmp_margin(reading, 432)) {
    // South-west.
    return 225.0f;
  }
  if (cmp_margin(reading, 647)) {
    // West.
    return 270.0f;
  }
  if (cmp_margin(reading, 607)) {
    // North-west.
    return 315.0f;
  }

  // Then the 8 minor directions.
  if (cmp_margin(reading, 280)) {
    // North north-east.
    return 22.5f;
  }
  if (cmp_margin(reading, 57)) {
    // East north-east.
    return 67.5f;
  }
  if (cmp_margin(reading, 44)) {
    // East south-east.
    return 112.5f;
  }
  if (cmp_margin(reading, 87)) {
    // South south-east.
    return 157.5f;
  }
  if (cmp_margin(reading, 168)) {
    // South south-west.
    return 202.5f;
  }
  if (cmp_margin(reading, 410)) {
    // West south-west.
    return 247.5f;
  }
  if (cmp_margin(reading, 566)) {
    // West north-west.
    return 292.5f;
  }
  if (cmp_margin(reading, 481)) {
    // North north-west.
    return 337.5f;
  }

  return -1.0f;
}

const char* get_wind_direction_text() {
  const int reading = analogRead(WIND_DIRECTION_PIN);

  // Try the 8 major directions first.
  // Major directions are most commonly output by the
  // device.
  if (cmp_margin(reading, 539)) {
    return "north";
  }
  if (cmp_margin(reading, 318)) {
    return "north-east";
  }
  if (cmp_margin(reading, 63)) {
    return "east";
  }
  if (cmp_margin(reading, 127)) {
    return "south-east";
  }
  if (cmp_margin(reading, 197)) {
    return "south";
  }
  if (cmp_margin(reading, 432)) {
    return "south-west";
  }
  if (cmp_margin(reading, 647)) {
    return "west";
  }
  if (cmp_margin(reading, 607)) {
    return "north-west";
  }

  // Then the 8 minor directions.
  if (cmp_margin(reading, 280)) {
    return "north north-east";
  }
  if (cmp_margin(reading, 57)) {
    return "east north-east";
  }
  if (cmp_margin(reading, 44)) {
    return "east south-east";
  }
  if (cmp_margin(reading, 87)) {
    return "south south-east";
  }
  if (cmp_margin(reading, 168)) {
    return "south south-west";
  }
  if (cmp_margin(reading, 410)) {
    return "west south-west";
  }
  if (cmp_margin(reading, 566)) {
    return "west north-west";
  }
  if (cmp_margin(reading, 481)) {
    return "north north-west";
  }

  return "error";
}
