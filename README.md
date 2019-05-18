# pogoda
Weather station at my home.

Frontend: http://pogoda.osowski.info

## Setup
1. An Arduino board with sensors, periodically writes sensor data to
   the serial output (C++).
2. A Raspberry Pi, connected to the Arduino via USB, reads this
   data and pushes it to a Google Cloud Datastore database (Python).
3. A web frontend presents the data from the Datastore database
   (Python).
