#!/usr/bin/env python3

from google.cloud import datastore
import os
import time
import traceback

import config
import data_source

def create_datastore_client():
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GCP_CREDENTIALS
    return datastore.Client(project=config.GCP_PROJECT)

def get_and_insert_data(weather_data):
    """Retrieves data and inserts it into a DB, once."""
    rows_to_add = []
    def add_row(value_time, name):
        value, time = value_time
        if value is None:
            return
        if time is None:
            return
        rows_to_add.append((time, name, value))

    add_row(weather_data.temperature.get_with_timestamp(), "temperature")
    add_row(weather_data.humidity.get_with_timestamp(), "humidity")
    add_row(weather_data.water_level.get_with_timestamp(), "water_level")

    if rows_to_add:
        client = create_datastore_client()

        def create_entity(row):
            time, name, value = row
            key = client.key(config.GCP_KIND_PREFIX + name)
            reading_ent = datastore.Entity(key)
            reading_ent.update(dict(
                time=time,
                value=value,
            ))
            return reading_ent
        reading_ents = map(create_entity, rows_to_add)

        client.put_multi(reading_ents)

if __name__ == "__main__":
    weather_data = data_source.WeatherDataSource
    time.sleep(5.0)
    while True:
        try:
            get_and_insert_data(weather_data)
        except:
            print("Problem while inserting data")
            traceback.print_exc()
        time.sleep(config.LOGGER_INTERVAL_SEC)
