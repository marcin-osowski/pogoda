#!/usr/bin/env python

import sqlite3
import time
import traceback

import config
import data_source

def get_and_insert_data(weather_data):
    """Retrieves data and inserts it into a DB, once."""
    rows_to_add = []
    def add_row(value_time, name):
        value, time = value_time
        if value is None:
            return
        if time is None:
            return
        rows_to_add.append((time.isoformat(" "), name, value))

    add_row(weather_data.temperature.get_with_timestamp(), "temperature")
    add_row(weather_data.humidity.get_with_timestamp(), "humidity")

    if rows_to_add:
        with sqlite3.connect(config.SQLITE_DB) as conn:
            cur = conn.cursor()
            cur.executemany("""
                INSERT INTO readings (datetime, name, value)
                VALUES (?, ?, ?)""", rows_to_add)
            conn.commit()

if __name__ == "__main__":
    weather_data = data_source.WeatherDataSource
    time.sleep(5.0)
    while True:
        try:
            get_and_insert_data(weather_data)
        except:
            print "Problem while inserting data"
            traceback.print_exc()
        time.sleep(60.0)
        print ".",
