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

float WindSpeedMeasurement::average_wind_speed() const {
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

uint8_t get_wind_direction_now() {
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
    return 0;
  }
  if (cmp_margin(reading, 318)) {
    // North-east.
    return 1;
  }
  if (cmp_margin(reading, 63)) {
    // East.
    return 2;
  }
  if (cmp_margin(reading, 127)) {
    // South-east.
    return 3;
  }
  if (cmp_margin(reading, 197)) {
    // South.
    return 4;
  }
  if (cmp_margin(reading, 432)) {
    // South-west.
    return 5;
  }
  if (cmp_margin(reading, 647)) {
    // West.
    return 6;
  }
  if (cmp_margin(reading, 607)) {
    // North-west.
    return 7;
  }

  // Then the 8 minor directions.
  if (cmp_margin(reading, 280)) {
    // North north-east.
    return 8;
  }
  if (cmp_margin(reading, 57)) {
    // East north-east.
    return 9;
  }
  if (cmp_margin(reading, 44)) {
    // East south-east.
    return 10;
  }
  if (cmp_margin(reading, 87)) {
    // South south-east.
    return 11;
  }
  if (cmp_margin(reading, 168)) {
    // South south-west.
    return 12;
  }
  if (cmp_margin(reading, 410)) {
    // West south-west.
    return 13;
  }
  if (cmp_margin(reading, 566)) {
    // West north-west.
    return 14;
  }
  if (cmp_margin(reading, 481)) {
    // North north-west.
    return 15;
  }

  // Reading failed.
  return 255;
}

float wind_direction_to_degrees(const uint8_t direction_idx) {
  switch(direction_idx) {
    // The 8 major directions first.
    case 0:
      // North.
      return 0.0f;
    case 1:
      // North-east.
      return 45.0f;
    case 2:
      // East.
      return 90.0f;
    case 3:
      // South-east.
      return 135.0f;
    case 4:
      // South.
      return 180.0f;
    case 5:
      // South-west.
      return 225.0f;
    case 6:
      // West.
      return 270.0f;
    case 7:
      // North-west.
      return 315.0f;
  
    // Then the 8 minor directions.
    case 8:
      // North north-east.
      return 22.5f;
    case 9:
      // East north-east.
      return 67.5f;
    case 10:
      // East south-east.
      return 112.5f;
    case 11:
      // South south-east.
      return 157.5f;
    case 12:
      // South south-west.
      return 202.5f;
    case 13:
      // West south-west.
      return 247.5f;
    case 14:
      // West north-west.
      return 292.5f;
    case 15:
      // North north-west.
      return 337.5f;
  }

  // Invalid input.
  return 255;
}

const char* wind_direction_to_text(const uint8_t direction_idx) {
  // The 8 major directions first.
  switch (direction_idx) {
      case 0:
        return "north";
      case 1:
        return "north-east";
      case 2:
        return "east";
      case 3:
        return "south-east";
      case 4:
        return "south";
      case 5:
        return "south-west";
      case 6:
        return "west";
      case 7:
        return "north-west";

      // Then the 8 minor directions.
      case 8:
        return "north north-east";
      case 9:
        return "east north-east";
      case 10:
        return "east south-east";
      case 11:
        return "south south-east";
      case 12:
        return "south south-west";
      case 13:
        return "west south-west";
      case 14:
        return "west north-west";
      case 15:
        return "north north-west";
  }

  // Invalid input.
  return "error";
}

WindDirectionMeasurement::WindDirectionMeasurement() {
  for (int i = 0; i < NUM_WIND_DIRECTIONS; ++i) {
    directions_count[i] = 0;
  }
}

void WindDirectionMeasurement::next_measurement() {
  const uint8_t wind_direction_idx = get_wind_direction_now();
  if (wind_direction_idx < NUM_WIND_DIRECTIONS) {
    directions_count[wind_direction_idx]++;
  }
}

uint8_t WindDirectionMeasurement::most_common_direction() const {
  uint8_t most_common_direction = 255;
  uint16_t most_common_count = 0;
  for (int i = 0; i < NUM_WIND_DIRECTIONS; ++i) {
    if (directions_count[i] > most_common_count) {
      most_common_direction = i;
      most_common_count = directions_count[i];
    }
  }
  return most_common_direction;
}
