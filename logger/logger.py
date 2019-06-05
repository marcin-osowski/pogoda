#!/usr/bin/env python3

import datetime
from google.cloud import datastore
import os
import queue
import threading
import time

import arduino_interface
import config
import instance_config
import ping


def create_datastore_client():
    """Creates a Client, to connect to the Datastore DB."""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GCP_CREDENTIALS
    return datastore.Client(project=config.GCP_PROJECT)


def insert_into_cloud_db(client, kind, timestamp, value):
    """Inserts a single entry into the cloud DB."""
    key = client.key(kind)
    reading_ent = datastore.Entity(key)
    reading_ent.update(dict(timestamp=timestamp))
    if value is not None:
        reading_ent.update(dict(value=value))
    client.put(reading_ent)


def queue_consumer_loop(data_queue):
    """A loop: popping items from queue, inserting them into the cloud DB."""
    while True:
        try:
            client = create_datastore_client()
            while True:
                kind, timestamp, value = data_queue.get()
                written = False
                try:
                    insert_into_cloud_db(client, kind, timestamp, value)
                    written = True
                finally:
                    if not written:
                        # Put back in the readings queue
                        readings_queue.put((kind, timestamp, value))
        except Exception as e:
            print("Problem while inserting data into the cloud DB.")
            print(e)
            time.sleep(120.0)


if __name__ == "__main__":
    # A queue with data to be written to the DB.
    # Triples: {DB kind (name), timestamp, value}
    data_queue = queue.Queue()

    # Start a thread to scrape Arduino data.
    arduino_scraper_thread = threading.Thread(
        target=arduino_interface.arduino_scraper_loop,
        kwargs=dict(data_queue=data_queue)
    )
    arduino_scraper_thread.setDaemon(True)
    arduino_scraper_thread.start()

    # Start a thread to scrape connection quality data.
    conn_quality_scraper_thread = threading.Thread(
        target=ping.conn_quality_scraper_loop,
        kwargs=dict(data_queue=data_queue)
    )
    conn_quality_scraper_thread.setDaemon(True)
    conn_quality_scraper_thread.start()

    # Start popping items from the readings queue and inserting them into the DB.
    queue_consumer_loop()
