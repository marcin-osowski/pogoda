#!/usr/bin/env python

import bottle
from collections import defaultdict
from concurrent import futures
from datetime import datetime, timezone, timedelta
from google.cloud import datastore
import os
import time

import config

app = bottle.Bottle()
executor = futures.ThreadPoolExecutor(max_workers=20)


class BackendLatencyTimer(object):
    """A simple class to measure backend latency."""

    def __init__(self):
        self.total = timedelta()

    def __enter__(self):
        self._start = datetime.utcnow()

    def __exit__(self, *args):
        self.total += datetime.utcnow() - self._start


def create_datastore_client():
    """Creates a Datastore Client object."""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GCP_CREDENTIALS
    return datastore.Client(project=config.GCP_PROJECT)


def get_latest_reading(latency, client, name):
    """Returns the value and timestamp of the latest reading."""
    query = client.query(kind=config.GCP_KIND_PREFIX + name)
    query.order = ["-timestamp"]
    with latency:
        results = list(query.fetch(limit=1))

    if not results:
        return None, None
    result = results[0]
    if "value" not in result:
        return None, None
    value = result["value"]
    if "timestamp" not in result:
        return None, None
    timestamp = result["timestamp"]

    return value, timestamp


def get_last_readings(client, name, timedelta):
    """Returns values and timestamps of recent readings."""
    minimum_time = datetime.now(timezone.utc) - timedelta
    query = client.query(kind=config.GCP_KIND_PREFIX + name)
    query.add_filter("timestamp", ">=", minimum_time)
    query.order = ["timestamp"]
    parsed_results = []
    for entity in query.fetch():
        if "value" not in entity:
            continue
        if "timestamp" not in entity:
            continue
        parsed_results.append((entity["value"], entity["timestamp"]))
    return parsed_results


def abs_delta_seconds(first, second):
    delta = (second - first).total_seconds()
    return abs(delta)


def apply_smoothing(readings, minutes):
    """Applies a +- X min average to the readings."""
    output_readings = []
    for i, (value, timestamp) in enumerate(readings):
        surround_values = [value]

        fwd_idx = i + 1
        while fwd_idx < len(readings):
            fwd_value, fwd_timestamp = readings[fwd_idx]
            abs_time_delta = abs_delta_seconds(timestamp, fwd_timestamp)
            if abs_time_delta < minutes * 60:
                surround_values.append(fwd_value)
            else:
                break
            fwd_idx += 1

        back_idx = i - 1
        while back_idx >= 0:
            back_value, back_timestamp = readings[back_idx]
            abs_time_delta = abs_delta_seconds(timestamp, back_timestamp)
            if abs_time_delta < minutes * 60:
                surround_values.append(back_value)
            else:
                break
            back_idx -= 1

        average = sum(surround_values) / len(surround_values)
        output_readings.append((average, timestamp))

    return output_readings


def round_datetime(dt, minutes):
    discard = timedelta(
        minutes=dt.minute % minutes,
        seconds=dt.second,
        microseconds=dt.microsecond)
    dt -= discard
    if discard >= timedelta(minutes=(minutes / 2.0)):
        dt += timedelta(minutes=minutes)
    return dt


class HumidityAndTemperature(object):
    """Humidity and temperature around a certain point in time."""

    # Constants for the saturation vapor pressure formula.
    # From Lowe, P.R. and J.M. Ficke, 1974: "The computation
    # of saturation vapor pressure"
    _A0 = 6.107799961
    _A1 = 4.436518521e-1
    _A2 = 1.428945805e-2
    _A3 = 2.650648471e-4
    _A4 = 3.031240396e-6
    _A5 = 2.034080948e-8
    _A6 = 6.136820929e-11

    def __init__(self):
        self._humidities = []
        self._temperatures = []

    def add_hmdt(self, hmdt):
        self._humidities.append(hmdt)

    def add_temp(self, temp):
        self._temperatures.append(temp)

    def avg_hmdt(self):
        if not self._humidities:
            return None
        return sum(self._humidities) / len(self._humidities)

    def avg_temp(self):
        if not self._temperatures:
            return None
        return sum(self._temperatures) / len(self._temperatures)

    def saturation_vapor_pressure(self):
        """Computes the saturation vapor pressure in hPa."""
        temp = self.avg_temp()
        if temp is None:
            return None

        # Computing the polynomial
        result = HumidityAndTemperature._A6
        result *= temp
        result += HumidityAndTemperature._A5
        result *= temp
        result += HumidityAndTemperature._A4
        result *= temp
        result += HumidityAndTemperature._A3
        result *= temp
        result += HumidityAndTemperature._A2
        result *= temp
        result += HumidityAndTemperature._A1
        result *= temp
        result += HumidityAndTemperature._A0

        return result

    def vapor_pressure(self):
        """Computes the vapor pressure in hPa."""
        hmdt = self.avg_hmdt()
        if hmdt is None:
            return None

        svp = self.saturation_vapor_pressure()
        if svp is None:
            return None

        return (hmdt / 100.0) * svp


def compute_vapor_pressure(temp_history, hmdt_history):
    """Creates a time series with vapor pressure, in hPa."""
    # First we need to align the temperature history
    # with humidity history. We'll round to 10-minute
    # intervals.
    rounded_map = defaultdict(lambda: HumidityAndTemperature())
    for temp, time in temp_history:
        rounded_time = round_datetime(time, minutes=10)
        rounded_map[rounded_time].add_temp(temp)
    for hmdt, time in hmdt_history:
        rounded_time = round_datetime(time, minutes=10)
        rounded_map[rounded_time].add_hmdt(hmdt)

    vapor_pressure_history = []
    for time, hmdt_and_temp in rounded_map.items():
        vapor_pressure = hmdt_and_temp.vapor_pressure()
        if vapor_pressure is not None:
            vapor_pressure_history.append((vapor_pressure, time))
    vapor_pressure_history.sort(key=lambda x: x[1])

    return vapor_pressure_history


def date_to_seconds_ago(date):
    if date is None:
        return None
    time_ago = datetime.now(timezone.utc) - date
    return time_ago.total_seconds()


@app.get("/")
def root():
    latency = BackendLatencyTimer()
    client = create_datastore_client()
    temp, temp_date = get_latest_reading(latency, client, "temperature")
    hmdt, hmdt_date = get_latest_reading(latency, client, "humidity")
    pres, pres_date = get_latest_reading(latency, client, "pressure")

    temp_ago = date_to_seconds_ago(temp_date)
    hmdt_ago = date_to_seconds_ago(hmdt_date)
    pres_ago = date_to_seconds_ago(pres_date)
    if None in [temp_ago, hmdt_ago, pres_ago]:
        data_age = None
    else:
        data_age = max(temp_ago, hmdt_ago, pres_ago)

    if None in [hmdt, temp]:
        vapor_pres = None
    else:
        hmdt_and_temp = HumidityAndTemperature()
        hmdt_and_temp.add_hmdt(hmdt)
        hmdt_and_temp.add_temp(temp)
        vapor_pres = hmdt_and_temp.vapor_pressure()

    return bottle.template("root.tpl", dict(
        temp=temp,
        hmdt=hmdt,
        vapor_pres=vapor_pres,
        pres=pres,
        data_age=data_age,
        latency=latency.total,
    ))


@app.get("/charts")
def route_charts():
    latency = BackendLatencyTimer()
    with latency:
        client = create_datastore_client()
        temp_history = executor.submit(
            get_last_readings, client, "temperature", timedelta(days=1))
        hmdt_history = executor.submit(
            get_last_readings, client, "humidity", timedelta(days=1))
        pres_history = executor.submit(
            get_last_readings, client, "pressure", timedelta(days=1))
        water_history = executor.submit(
            get_last_readings, client, "water_level", timedelta(days=1))
        futures.wait([temp_history, hmdt_history, pres_history, water_history])

    # Vapor pressure is computed from temperature and humidity.
    vapor_pres_history = compute_vapor_pressure(
        temp_history.result(), hmdt_history.result())

    temp_history = apply_smoothing(temp_history.result(), minutes=5.1)
    hmdt_history = apply_smoothing(hmdt_history.result(), minutes=20.1)
    vapor_pres_history = apply_smoothing(vapor_pres_history, minutes=30.1)
    pres_history = apply_smoothing(pres_history.result(), minutes=20.1)
    water_history = apply_smoothing(water_history.result(), minutes=20.1)

    return bottle.template("charts.tpl", dict(
        temp_history=temp_history,
        hmdt_history=hmdt_history,
        vapor_pres_history=vapor_pres_history,
        pres_history=pres_history,
        water_history=water_history,
        latency=latency.total,
    ))


@app.get("/static/<filepath:path>")
def route_static(filepath):
        return bottle.static_file(filepath, root="staticdata/")
