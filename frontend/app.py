#!/usr/bin/env python

import bottle
from collections import defaultdict
from concurrent import futures
from datetime import datetime, timezone, timedelta
import math
import time

import config
import db_access

app = bottle.Bottle()
executor = futures.ThreadPoolExecutor(max_workers=40)


class BackendLatencyTimer(object):
    """A simple class to measure backend latency."""

    def __init__(self):
        self.total = timedelta()

    def __enter__(self):
        self._start = datetime.now(timezone.utc)

    def __exit__(self, *args):
        self.total += datetime.now(timezone.utc) - self._start


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


def insert_gaps(readings, min_gap_minutes):
    """Inserts gaps into the readings.

    If there's a reading gap of at least `min_gap_minutes` minutes."""
    output_readings = []
    if not readings:
        return output_readings
    output_readings.append(readings[0])
    for i in range(1, len(readings)):
        _, prev_timestamp = readings[i - 1]
        curr_value, curr_timestamp = readings[i]
        minutes_passed = (curr_timestamp - prev_timestamp).total_seconds() / 60.0
        if minutes_passed > min_gap_minutes:
            gap_delay = timedelta(minutes=(minutes_passed / 2.0))
            gap_timestamp = prev_timestamp + gap_delay
            output_readings.append((None, gap_timestamp))
        output_readings.append((curr_value, curr_timestamp))

    return output_readings


def multiply_series(readings, multiplier):
    """Multiplies all values in the series by a constant."""
    output_readings = []
    for value, timestamp in readings:
        if value is None:
            output_readings.append((None, timestamp))
        else:
            output_readings.append((value * multiplier, timestamp))
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


def dew_point_from_vapor_pressure(vapor_pressure):
    """Computes the dew point, in deg C.

    Takes vapor pressure in hPa.
    """
    # Formula from Wikipedia:
    # https://en.wikipedia.org/wiki/Dew_point
    pa = vapor_pressure
    a = 6.1121
    b = 18.678
    c = 257.14

    pa_a = pa / a
    log_pa_a = math.log(pa_a)

    return c * log_pa_a / (b - log_pa_a)


def compute_dew_point(vapor_pressure_history):
    """Creates a time series with dew point, in deg C.

    Takes a time series with vapor pressure in hPa.
    """
    dew_point_history = []
    for vapor_pressure, time in vapor_pressure_history:
        if None in [vapor_pressure, time]:
            continue
        dew_point = dew_point_from_vapor_pressure(vapor_pressure)
        dew_point_history.append((dew_point, time))

    return dew_point_history


def date_to_seconds_ago(date):
    if date is None:
        return None
    time_ago = datetime.now(timezone.utc) - date
    return time_ago.total_seconds()


def degrees_to_direction_name(degrees):
    if degrees is None:
        return None
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = int((degrees + 11.25) / 22.5)
    return dirs[ix % 16]


@app.get("/")
def root():
    latency = BackendLatencyTimer()
    with latency:
        client = db_access.get_datastore_client()
        temp_and_date = executor.submit(
            db_access.get_latest_reading, client, config.GCP_TEMP_KIND)
        hmdt_and_date = executor.submit(
            db_access.get_latest_reading, client, config.GCP_HMDT_KIND)
        pres_and_date = executor.submit(
            db_access.get_latest_reading, client, config.GCP_PRES_KIND)
        pm_25_and_date = executor.submit(
            db_access.get_latest_reading, client, config.GCP_PM25_KIND)
        wnd_speed_and_date = executor.submit(
            db_access.get_latest_reading, client, config.GCP_WND_SPEED_KIND)
        wnd_dir_and_date = executor.submit(
            db_access.get_latest_reading, client, config.GCP_WND_DIR_KIND)
        temp, temp_date = temp_and_date.result()
        hmdt, hmdt_date = hmdt_and_date.result()
        pres, pres_date = pres_and_date.result()
        pm_25, pm_25_date = pm_25_and_date.result()
        wnd_speed, wnd_speed_date = wnd_speed_and_date.result()
        wnd_dir, wnd_dir_date = wnd_dir_and_date.result()

    dates = [temp_date, hmdt_date, pres_date, wnd_speed_date, wnd_dir_date]
    if None in dates:
        data_age = None
    else:
        agos = map(date_to_seconds_ago, dates)
        data_age = max(agos)

    if None in [hmdt, temp]:
        vapor_pres = None
        dew_point = None
    else:
        hmdt_and_temp = HumidityAndTemperature()
        hmdt_and_temp.add_hmdt(hmdt)
        hmdt_and_temp.add_temp(temp)
        vapor_pres = hmdt_and_temp.vapor_pressure()
        dew_point = dew_point_from_vapor_pressure(vapor_pres)

    wnd_dir_text = degrees_to_direction_name(wnd_dir)

    return bottle.template("root.tpl", dict(
        temp=temp,
        hmdt=hmdt,
        vapor_pres=vapor_pres,
        dew_point=dew_point,
        pres=pres,
        pm_25=pm_25,
        wnd_speed=wnd_speed,
        wnd_dir=wnd_dir,
        wnd_dir_text=wnd_dir_text,
        data_age=data_age,
        latency=latency.total,
    ))


class ChartData(object):
    """A helper struct to hold chart data."""

    def __init__(self, name, description, history):
        self.name = name
        self.description = description
        self.history = history


@app.get("/charts")
def route_charts():
    latency = BackendLatencyTimer()
    time_to = datetime.now(timezone.utc)
    time_from = time_to - timedelta(days=1)
    with latency:
        client = db_access.get_datastore_client()
        temp_history = executor.submit(
            db_access.get_last_readings, client, config.GCP_TEMP_KIND,
            time_from, time_to)
        hmdt_history = executor.submit(
            db_access.get_last_readings, client, config.GCP_HMDT_KIND,
            time_from, time_to)
        pres_history = executor.submit(
            db_access.get_last_readings, client, config.GCP_PRES_KIND,
            time_from, time_to)
        pm_25_history = executor.submit(
            db_access.get_last_readings, client, config.GCP_PM25_KIND,
            time_from, time_to)
        wnd_speed_history = executor.submit(
            db_access.get_last_readings, client, config.GCP_WND_SPEED_KIND,
            time_from, time_to)
        wnd_dir_history = executor.submit(
            db_access.get_last_readings, client, config.GCP_WND_DIR_KIND,
            time_from, time_to)
        temp_history = temp_history.result()
        hmdt_history = hmdt_history.result()
        pres_history = pres_history.result()
        pm_25_history = pm_25_history.result()
        wnd_speed_history = wnd_speed_history.result()
        wnd_dir_history = wnd_dir_history.result()

    # Vapor pressure and dew point are computed
    # from temperature and humidity.
    vapor_pres_history = compute_vapor_pressure(temp_history, hmdt_history)
    dew_point_history = compute_dew_point(vapor_pres_history)

    # Smoothen the data.
    temp_history = apply_smoothing(temp_history, minutes=20.1)
    hmdt_history = apply_smoothing(hmdt_history, minutes=20.1)
    vapor_pres_history = apply_smoothing(vapor_pres_history, minutes=30.1)
    dew_point_history = apply_smoothing(dew_point_history, minutes=30.1)
    pres_history = apply_smoothing(pres_history, minutes=20.1)
    pm_25_history = apply_smoothing(pm_25_history, minutes=40.1)
    wnd_speed_history = apply_smoothing(wnd_speed_history, minutes=20.1)

    # Insert gaps.
    temp_history = insert_gaps(temp_history, min_gap_minutes=20.1)
    hmdt_history = insert_gaps(hmdt_history, min_gap_minutes=20.1)
    vapor_pres_history = insert_gaps(vapor_pres_history, min_gap_minutes=20.1)
    dew_point_history = insert_gaps(dew_point_history, min_gap_minutes=20.1)
    pres_history = insert_gaps(pres_history, min_gap_minutes=20.1)
    pm_25_history = insert_gaps(pm_25_history, min_gap_minutes=20.1)
    wnd_speed_history = insert_gaps(wnd_speed_history, min_gap_minutes=20.1)
    wnd_dir_history = insert_gaps(wnd_dir_history, min_gap_minutes=20.1)

    # Wrap it together in a single list.
    chart_datas = []
    chart_datas.append(ChartData(
        name="temp", description="Temperature [°C]",
        history=temp_history))
    chart_datas.append(ChartData(
        name="hmdt", description="Humidity [%]",
        history=hmdt_history))
    chart_datas.append(ChartData(
        name="vapor_pres", description="Vapor pressure [hPa]",
        history=vapor_pres_history))
    chart_datas.append(ChartData(
        name="dew_point", description="Dew point [°C]",
        history=dew_point_history))
    chart_datas.append(ChartData(
        name="pres", description="Pressure [hPa]",
        history=pres_history))
    chart_datas.append(ChartData(
        name="wnd_speed", description="Wind speed [m/s]",
        history=wnd_speed_history))
    chart_datas.append(ChartData(
        name="wnd_dir", description="Wind direction [degrees]",
        history=wnd_dir_history))
    chart_datas.append(ChartData(
        name="pm_25", description="PM 2.5 [μg/m³]",
        history=pm_25_history))

    return bottle.template("charts.tpl", dict(
        chart_datas=chart_datas,
        time_from=time_from,
        time_to=time_to,
        latency=latency.total,
    ))


@app.get("/devices")
def route_devices():
    latency = BackendLatencyTimer()
    time_to = datetime.now(timezone.utc)
    time_from = time_to - timedelta(days=1)
    with latency:
        client = db_access.get_datastore_client()
        ground_latency = executor.submit(
            db_access.get_last_readings,
            client, config.GCP_GROUND_INTERNET_LATENCY_KIND,
            time_from, time_to)
        ground_db_latency = executor.submit(
            db_access.get_last_readings,
            client, config.GCP_GROUND_DB_LATENCY_KIND,
            time_from, time_to)
        ground_db_success = executor.submit(
            db_access.get_last_readings,
            client, config.GCP_GROUND_DB_SUCCESS_RATE_KIND,
            time_from, time_to)
        ground_arduino_bps = executor.submit(
            db_access.get_last_readings,
            client, config.GCP_GROUND_ARDUINO_BPS,
            time_from, time_to)
        ground_latency = ground_latency.result()
        ground_db_latency = ground_db_latency.result()
        ground_db_success = ground_db_success.result()
        ground_arduino_bps = ground_arduino_bps.result()

    # Scale from seconds to miliseconds
    ground_latency = multiply_series(ground_latency, 1000.0)
    ground_db_latency = multiply_series(ground_db_latency, 1000.0)

    # Insert gaps.
    ground_latency = insert_gaps(ground_latency, min_gap_minutes=30.1)
    ground_db_latency = insert_gaps(ground_db_latency, min_gap_minutes=30.1)
    ground_db_success = insert_gaps(ground_db_success, min_gap_minutes=30.1)
    ground_arduino_bps = insert_gaps(ground_arduino_bps, min_gap_minutes=30.1)

    # Gather charts
    chart_datas = []
    chart_datas.append(ChartData(
        name="ground_db_latency",
        description="Ground level: cloud DB write latency [ms]",
        history=ground_db_latency,
    ))
    chart_datas.append(ChartData(
        name="ground_db_success",
        description="Ground level: cloud DB write success rate",
        history=ground_db_success,
    ))
    chart_datas.append(ChartData(
        name="ground_arduino_bps",
        description="Ground level: Arduino comm output speed [bytes/sec]",
        history=ground_arduino_bps,
    ))
    chart_datas.append(ChartData(
        name="ground_internet_latency",
        description="Ground level: internet latency [ms]",
        history=ground_latency,
    ))

    return bottle.template("devices.tpl", dict(
        chart_datas=chart_datas,
        time_from=time_from,
        time_to=time_to,
        latency=latency.total,
    ))


@app.get("/static/<filepath:path>")
def route_static(filepath):
        return bottle.static_file(filepath, root="staticdata/")
