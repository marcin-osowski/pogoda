#!/usr/bin/env python

import bottle
import bottle.ext.sqlite
import datetime
import time

import config

app = bottle.Bottle()
sqlite_plugin = bottle.ext.sqlite.Plugin(dbfile=config.SQLITE_DB)
app.install(sqlite_plugin)

def parse_datetime(str_date):
    return datetime.datetime.strptime(str_date, "%Y-%m-%d %H:%M:%S.%f")

def get_latest_reading(db, name):
    """Returns the value and timestamp of the latest reading."""
    cur = db.cursor()
    results = cur.execute("""
        SELECT value, datetime
        FROM readings
        WHERE name = ?
        ORDER BY datetime DESC
        LIMIT 1
    """, (name,)).fetchone()
    if not results:
        return None, None
    (value, datetime_text) = results
    datetime = parse_datetime(datetime_text)
    return value, datetime

def get_last_readings(db, name, timedelta):
    """Returns values and timestamps of recent readings."""
    minimum_time = datetime.datetime.utcnow() - timedelta
    minimum_time = minimum_time.isoformat(" ")
    cur = db.cursor()
    results = cur.execute("""
        SELECT value, datetime
        FROM readings
        WHERE name = ?
            AND datetime >= ?
        ORDER BY datetime ASC
    """, (name, minimum_time))
    parsed_results = []
    for value, datetime_text in results:
        parsed_results.append((value, parse_datetime(datetime_text)))
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

def date_to_seconds_ago(date):
    time_ago = datetime.datetime.utcnow() - date
    return time_ago.total_seconds()

@app.get("/")
def root(db):
    temp, temp_date = get_latest_reading(db, "temperature")
    hmdt, hmdt_date = get_latest_reading(db, "humidity")

    temp_ago = date_to_seconds_ago(temp_date)
    hmdt_ago = date_to_seconds_ago(hmdt_date)
    data_age = max(temp_ago, hmdt_ago)

    return bottle.template("root.tpl", dict(
        temp=temp,
        hmdt=hmdt,
        data_age=data_age,
    ))

@app.get("/charts")
def route_charts(db):
    temp_history = get_last_readings(db, "temperature", datetime.timedelta(days=1))
    hmdt_history = get_last_readings(db, "humidity", datetime.timedelta(days=1))
    water_history = get_last_readings(db, "water_level", datetime.timedelta(days=1))

    temp_history = apply_smoothing(temp_history, minutes=5.0)
    hmdt_history = apply_smoothing(hmdt_history, minutes=20.0)
    water_history = apply_smoothing(water_history, minutes=20.0)

    return bottle.template("charts.tpl", dict(
        temp_history=temp_history,
        hmdt_history=hmdt_history,
        water_history=water_history,
    ))

@app.get("/static/<filepath:path>")
def route_static(filepath):
        return bottle.static_file(filepath, root="staticdata/")
