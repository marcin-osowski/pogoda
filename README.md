# pogoda
Weather station at my home.

Frontend: https://pogoda.osowski.info

## Setup
1. `arduino_ground/`: an Arduino Nano board connected to sensors,
   periodically writes sensor data to the serial output (C++).
   Located at ground level (around 1 meter above the ground).
   Sensors: temperature, humidity, air pressure, air quality.
2. `arduino_roof/`: obsolete
3. `logger/`: a Raspberry Pi, connected to the Arduino via USB,
   reads this data and pushes it to a Google Cloud Datastore
   database (Python).
4. `frontend/`: a web server, presents the data from the
   Datastore database (Python).

## Running sensors
1. Temperature and humidity:
   [AM2301](https://kropochev.com/downloads/humidity/AM2301.pdf)
2. Air pressure:
   [BMP085](https://www.sparkfun.com/datasheets/Components/General/BST-BMP085-DS000-05.pdf)
3. Air quality (particulate matter):
   [PMS5003](https://cdn-learn.adafruit.com/downloads/pdf/pm25-air-quality-sensor.pdf)
