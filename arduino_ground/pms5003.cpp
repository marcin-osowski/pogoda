#include "pms5003.h"

// Copied from Adafruit's code.
bool readPMSdata(SoftwareSerial* serial, struct pms5003data* data) {
  if (!serial->available()) {
    return false;
  }

  // Read a byte at a time until we get to the special '0x42' start-byte
  if (serial->peek() != 0x42) {
    serial->read();
    return false;
  }

  // Now read all 32 bytes
  if (serial->available() < 32) {
    return false;
  }

  uint8_t buffer[32];
  uint16_t sum = 0;
  serial->readBytes(buffer, 32);

  // get checksum ready
  for (uint8_t i=0; i<30; i++) {
    sum += buffer[i];
  }

  // The data comes in endian'd, this solves it so it works on all platforms
  uint16_t buffer_u16[15];
  for (uint8_t i=0; i<15; i++) {
    buffer_u16[i] = buffer[2 + i*2 + 1];
    buffer_u16[i] += (buffer[2 + i*2] << 8);
  }

  // put it into a nice struct :)
  memcpy((void *)data, (void *)buffer_u16, 30);

  if (sum != data->checksum) {
    // Checksum failure.
    return false;
  }

  // success!
  return true;
}
