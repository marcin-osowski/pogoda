/*

An Arduino controller for the weather station, installed
at the roof. Output is ritten to the serial port with
SERIAL_BAUD speed, in the following form:
  - TODO

Units:
  - TODO

Pin layout (for Arduino Nano):
  - D2: anemometer. Other wire from the anemometer should
        be connected to the ground.
  - D3: rain gauge. Other wire from the rain gauge should
        be connected to the ground.
  - A4: wind direction sensor. A4 should be connected via a
        10k resistor to VCC. The other wire from the wind
        direction sensor should be connected to the ground.

*/

// Output is written to serial.
#define SERIAL_BAUD 9600

// Anemometer connection
#define ANEMO_PIN 2

// Rain gauge connection
#define RAIN_PIN 3

// Wind direction connection
#define WIND_DIRECTION_PIN A4

// Number of quiet microsecons required to register a new
// interrupt (both for anemo and rain).
#define INTERRUPT_DEBOUNCE_US 5000

// Interrupt handler for the anemometer.
volatile unsigned long last_time_anemo = 0;
volatile uint32_t anemo_interrupts = 0;
void anemo_interrupt_handler() {
  const unsigned long time_since_last = micros() - last_time_anemo;
  last_time_anemo = micros();

  if (time_since_last > INTERRUPT_DEBOUNCE_US) {
    anemo_interrupts++;
  }
}

// A function that correctly reads the
// current amount of anemo interrupts.
uint32_t get_anemo_interrupt_count() {
  noInterrupts();
  volatile uint32_t anemo_copy = anemo_interrupts;
  interrupts();
  return anemo_copy;
}

// Interrupt handler for the rain gauge.
volatile unsigned long last_time_rain = 0;
volatile unsigned long rain_interrupts = 0;
void rain_interrupt_handler() {
  const unsigned long time_since_last = micros() - last_time_rain;
  last_time_rain = micros();

  if (time_since_last > INTERRUPT_DEBOUNCE_US) {
    rain_interrupts++;
  }
}

// A function that correctly reads the
// current amount of rain interrupts.
uint32_t get_rain_interrupt_count() {
  noInterrupts();
  volatile uint32_t rain_copy = rain_interrupts;
  interrupts();
  return rain_copy;
}

void setup() {
  // Initializes the output seral port.
  Serial.begin(SERIAL_BAUD);
  while (!Serial);

  // Set up anemometer and rain gauge pins.
  pinMode(ANEMO_PIN, INPUT_PULLUP);
  pinMode(RAIN_PIN, INPUT_PULLUP);

  // Wait a while for the values to settle.
  delay(100);

  // Attach anemo and rain interrupt handlers.
  attachInterrupt(
    digitalPinToInterrupt(ANEMO_PIN),
    anemo_interrupt_handler,
    RISING);
  attachInterrupt(
    digitalPinToInterrupt(RAIN_PIN),
    rain_interrupt_handler,
    RISING);

  // Wait a little more and clear the interrupt counts.
  // For unknown reason there are spurious interrupts
  // around startup.
  delay(100);
  noInterrupts();
  rain_interrupts = 0;
  anemo_interrupts = 0;
  interrupts();
}

void loop() {
  delay(1000);
  const int a = analogRead(WIND_DIRECTION_PIN);
  Serial.print("Rain: ");
  Serial.println(get_rain_interrupt_count());
  Serial.print("Anemo: ");
  Serial.println(get_anemo_interrupt_count());
  Serial.print("Direction (raw read): ");
  Serial.println(a);
}
