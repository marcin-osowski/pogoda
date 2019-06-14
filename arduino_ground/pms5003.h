#include <Arduino.h>
#include <SoftwareSerial.h>

// For the air quality sensor.
// Copied from Adafruit's code.
struct pms5003data {
  uint16_t framelen;
  uint16_t pm10_standard, pm25_standard, pm100_standard;
  uint16_t pm10_env, pm25_env, pm100_env;
  uint16_t particles_03um, particles_05um, particles_10um, particles_25um, particles_50um, particles_100um;
  uint16_t unused;
  uint16_t checksum;
};

// Reads PMS5003 output.
// Returns false if reading fails (for example there's
// currently no data to read).
bool readPMSdata(SoftwareSerial* serial, struct pms5003data* data);
