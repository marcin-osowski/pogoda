#!/usr/bin/env python

import bottle
import bottle.ext.sqlite
import datetime
import time

import config

app = bottle.Bottle()
sqlite_plugin = bottle.ext.sqlite.Plugin(dbfile=config.SQLITE_DB)
app.install(sqlite_plugin)

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
    (value, datetime) = results
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
    return results.fetchall()

def apply_moving_average(readings):
    """Applies a 10-point moving average to the readings."""
    recent_values = []
    output_readings = []
    for value, timestamp in readings:
        recent_values.append(value)
        if len(recent_values) > 10:
            recent_values.pop(0)
        average = sum(recent_values) / len(recent_values)
        output_readings.append((average, timestamp))
    return output_readings

def string_date_to_seconds_ago(str_date):
    if str_date is None:
        return "unknown"
    parsed_date = datetime.datetime.strptime(str_date, "%Y-%m-%d %H:%M:%S.%f")
    time_ago = datetime.datetime.utcnow() - parsed_date
    return time_ago.total_seconds()

@app.get("/")
def root(db):
    temp, temp_date = get_latest_reading(db, "temperature")
    hmdt, hmdt_date = get_latest_reading(db, "humidity")

    temp_ago = string_date_to_seconds_ago(temp_date)
    hmdt_ago = string_date_to_seconds_ago(hmdt_date)
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

    temp_history = apply_moving_average(temp_history)
    hmdt_history = apply_moving_average(hmdt_history)

    return bottle.template("charts.tpl", dict(
        temp_history=temp_history,
        hmdt_history=hmdt_history,
    ))

@app.get("/static/<filepath:path>")
def route_static(filepath):
        return bottle.static_file(filepath, root="staticdata/")
