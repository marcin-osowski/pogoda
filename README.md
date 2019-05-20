# pogoda
Weather station at my home.

Frontend: https://pogoda.osowski.info

## Setup
1. `arduino_controller/`: an Arduino Nano board connected to sensors,
   periodically writes sensor data to the serial output (C++).
2. `logger/`: a Raspberry Pi, connected to the Arduino via USB,
   reads this data and pushes it to a Google Cloud Datastore
   database (Python).
3. `frontend/`: a web server, presents the data from the
   Datastore database (Python).

## Used sensors
1. Temperature and humidity:
   [AM2301](https://kropochev.com/downloads/humidity/AM2301.pdf)
2. Air pressure:
   [BMP085](https://www.sparkfun.com/datasheets/Components/General/BST-BMP085-DS000-05.pdf)
