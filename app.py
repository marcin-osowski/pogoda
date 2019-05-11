#!/usr/bin/env python

import bottle
import time

import data_source

weather_data = data_source.WeatherDataSource
app = bottle.Bottle()

@app.get("/")
def root():
    temperature = weather_data.temperature.get()
    humidity = weather_data.humidity.get()

    return bottle.template("root.tpl", dict(
        temperature=temperature,
        humidity=humidity,
    ))

    result = ["Weather station"]

    if temperature is not None:
        result.append("Temperature: %.1f C" % temperature)
    if humidity is not None:
        result.append("Humidity: %.0f %%" % humidity)

    return "<br>".join(result)

@app.get('/static/<filepath:path>')
def route_static(filepath):
        return bottle.static_file(filepath, root='staticdata/')
