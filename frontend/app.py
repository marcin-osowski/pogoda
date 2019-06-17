#!/usr/bin/env python

import bottle
from collections import defaultdict
from concurrent import futures
from datetime import datetime, timezone, timedelta
import math
import pysolar
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

def compute_sun_altitude(time):
    return pysolar.solar.get_altitude(
        config.SITE_LATITUDE,
        config.SITE_LONGITUDE,
        time,
    )


def generate_sun_altitude_series(time_from, time_to, num_points=101):
    """Generates a time series with sun's altitude."""
    time_per_point = (time_to - time_from)/(num_points - 1)
    series = []
    for i in range(num_points):
        point_time = time_from + (time_per_point * i)
        sun_altitude = compute_sun_altitude(point_time)
        series.append((sun_altitude, point_time))

    return series


def compute_sun_radiation_power_series(sun_altitude_series):
    """Compute sun's radiation power using sun's altitude."""
    output = []
    for altitude, time in sun_altitude_series:
        if altitude <= 0.0:
            radiation = 0.0
        else:
            radiation = pysolar.radiation.get_radiation_direct(time, altitude)
        output.append((radiation, time))

    return output


def align_cumulative_measure(input_series):
    """Aligns the cumulative measure."""
    output = []
    to_add = 0.0
    prev_value = 0.0
    for value, time in input_series:
        if prev_value > value:
            # Value reset detected.
            to_add += prev_value
        output.append((value + to_add, time))
        prev_value = value

    return output


def differentiate_cumulative_measure(input_series, time_from, time_to, num_buckets=100):
    """Differentiates a cumulative measure into num_buckets buckets."""
    if len(input_series) < 2:
        return None

    time_step = (time_to - time_from) / num_buckets
    last_value = input_series[0][0]
    i = 1
    output = []
    for step in range(num_buckets):
        start_time = time_from + (time_step * (step))
        mid_time = time_from + (time_step * (step + 0.5))
        end_time = time_from + (time_step * (step + 1))
        start_offset = i

        # Find the first element that's after end_time.
        while (i < len(input_series) and input_series[i][1] < end_time):
            i += 1

        end_offset = i

        if start_offset == end_offset:
            # No points in the range. Output a None value.
            output.append((None, mid_time))
        else:
            value_in_bucket = input_series[i - 1][0] - last_value
            last_value = input_series[i - 1][0]
            output.append((value_in_bucket, mid_time))

    return output


def date_to_seconds_ago(date):
    if date is None:
        return None
    time_ago = datetime.now(timezone.utc) - date
    return time_ago.total_seconds()


def degrees_to_direction_name(degrees):
    if degrees is None:
        return None
    dirs = [
      "North", "North North-East", "North-East", "East North-East",
      "East", "East South-East", "South-East", "South South-East",
      "South", "South South-West", "South-West", "West South-West",
      "West", "West North-West", "North-West", "North North-West",
    ]
    ix = int((degrees + 11.25) / 22.5)
    return dirs[ix % 16]


@app.get("/")
def root():
    latency = BackendLatencyTimer()
    rain_time_to = datetime.now(timezone.utc)
    rain_time_from = rain_time_to - timedelta(days=1)
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
        cumulative_rain_history = executor.submit(
            db_access.get_last_readings, client, config.GCP_RAIN_MM_KIND,
            rain_time_from, rain_time_to)
        temp, temp_date = temp_and_date.result()
        hmdt, hmdt_date = hmdt_and_date.result()
        pres, pres_date = pres_and_date.result()
        pm_25, pm_25_date = pm_25_and_date.result()
        wnd_speed, wnd_speed_date = wnd_speed_and_date.result()
        wnd_dir, wnd_dir_date = wnd_dir_and_date.result()
        cumulative_rain_history = cumulative_rain_history.result()

    # Align cumulative measures.
    cumulative_rain_history = align_cumulative_measure(cumulative_rain_history)

    if len(cumulative_rain_history) < 2:
        rain_past_day = None
    else:
        rain_past_day = cumulative_rain_history[-1][0] - cumulative_rain_history[0][0]

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
        rain_past_day=rain_past_day,
        data_age=data_age,
        latency=latency.total,
    ))


class ChartData(object):
    """A helper struct to hold chart data."""

    def __init__(self, name, description, history, chart_type="LineChart"):
        self.name = name
        self.description = description
        self.history = history
        self.chart_type = chart_type


@app.get("/charts")
def route_charts():
    latency = BackendLatencyTimer()
    time_to = datetime.now(timezone.utc)
    time_from = time_to - timedelta(days=2)
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
        cumulative_rain_history = executor.submit(
            db_access.get_last_readings, client, config.GCP_RAIN_MM_KIND,
            time_from, time_to)
        temp_history = temp_history.result()
        hmdt_history = hmdt_history.result()
        pres_history = pres_history.result()
        pm_25_history = pm_25_history.result()
        wnd_speed_history = wnd_speed_history.result()
        wnd_dir_history = wnd_dir_history.result()
        cumulative_rain_history = cumulative_rain_history.result()

    # Align cumulative measures.
    cumulative_rain_history = align_cumulative_measure(cumulative_rain_history)

    # Differentiate rain history, for an area chart.
    rain_history = differentiate_cumulative_measure(
        cumulative_rain_history, time_from=time_from, time_to=time_to)

    # Compute sun's altitude and radiation power.
    sun_altitude_computed = generate_sun_altitude_series(time_from, time_to)
    sun_radiation_computed = compute_sun_radiation_power_series(sun_altitude_computed)

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
        name="wnd_dir", description="Wind direction [°]",
        history=wnd_dir_history))
    chart_datas.append(ChartData(
        name="rain_history", description="Rain [mm]",
        history=rain_history, chart_type="SteppedAreaChart"))
    chart_datas.append(ChartData(
        name="pm_25", description="PM 2.5 [μg/m³]",
        history=pm_25_history))
    chart_datas.append(ChartData(
        name="sun_altitude", description="Computed altitude of the Sun [°]",
        history=sun_altitude_computed))
    chart_datas.append(ChartData(
        name="sun_radiation_power",
        description="Computed clear sky radiation power of the Sun [W/m²]",
        history=sun_radiation_computed))

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
    time_from = time_to - timedelta(days=2)
    with latency:
        client = db_access.get_datastore_client()
        data_by_logger = dict()

        # Request data
        for logger_name, (logger_gcp_prefix, _) in config.MONITORED_LOGGERS.items():
            logger_data = dict()
            logger_data["latency"] = executor.submit(
                db_access.get_last_readings,
                client, logger_gcp_prefix + config.GCP_INTERNET_LATENCY,
                time_from, time_to)
            logger_data["db_latency"] = executor.submit(
                db_access.get_last_readings,
                client, logger_gcp_prefix + config.GCP_DB_LATENCY,
                time_from, time_to)
            logger_data["db_success"] = executor.submit(
                db_access.get_last_readings,
                client, logger_gcp_prefix + config.GCP_DB_SUCCESS_RATE,
                time_from, time_to)
            logger_data["arduino_bps"] = executor.submit(
                db_access.get_last_readings,
                client, logger_gcp_prefix + config.GCP_ARDUINO_BPS,
                time_from, time_to)
            data_by_logger[logger_name] = logger_data

        # Get data
        for logger_name, datas in data_by_logger.items():
            for name in list(datas.keys()):
                datas[name] = datas[name].result()

    # Scale from seconds to miliseconds
    for logger_name, datas in data_by_logger.items():
        datas["latency"] = multiply_series(datas["latency"], 1000.0)
        datas["db_latency"] = multiply_series(datas["db_latency"], 1000.0)

    # Insert gaps.
    for _, datas in data_by_logger.items():
        for name in list(datas.keys()):
            datas[name] = insert_gaps(datas[name], min_gap_minutes=30.1)

    # Gather charts
    charts_by_logger = []
    for logger_name, (_, logger_description) in config.MONITORED_LOGGERS.items():
        datas = data_by_logger[logger_name]
        logger_charts = []
        logger_charts.append(ChartData(
            name=logger_name + "_db_latency",
            description="Cloud DB write latency [ms]",
            history=datas["db_latency"],
        ))
        logger_charts.append(ChartData(
            name=logger_name + "db_success",
            description="Cloud DB write success rate",
            history=datas["db_success"],
        ))
        logger_charts.append(ChartData(
            name=logger_name + "_arduino_bps",
            description="Arduino comm output speed [bytes/sec]",
            history=datas["arduino_bps"],
        ))
        logger_charts.append(ChartData(
            name=logger_name + "_internet_latency",
            description="Internet latency [ms]",
            history=datas["latency"],
        ))
        charts_by_logger.append((logger_name, logger_description, logger_charts))

    # Sort to have predictable order of the charts.
    charts_by_logger.sort()

    return bottle.template("devices.tpl", dict(
        charts_by_logger=charts_by_logger,
        time_from=time_from,
        time_to=time_to,
        latency=latency.total,
    ))


@app.get("/static/<filepath:path>")
def route_static(filepath):
        return bottle.static_file(filepath, root="staticdata/")
