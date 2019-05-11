#!/usr/bin/env python

import data_source
import time

if __name__ == "__main__":
    weather_data = data_source.WeatherDataSource()

    while True:
        time.sleep(2.0)
        temperature = weather_data.temperature.get()
        humidity = weather_data.humidity.get()

        if temperature is not None:
            print "Temperature: %.1f C" % temperature
        if humidity is not None:
            print "Humidity: %.0f %%" % humidity

    time.sleep(60.0)
