# pogoda
Weather station at my home.

Frontend: http://pogoda.osowski.info

## Setup
1. `arduino_controller/`: an Arduino board with sensors,
   periodically writes sensor data to the serial output (C++).
2. `logger/`: a Raspberry Pi, connected to the Arduino via USB,
   reads this data and pushes it to a Google Cloud Datastore
   database (Python).
3. `frontend/`: a web server, presents the data from the
   Datastore database (Python).
