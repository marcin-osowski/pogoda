#!/usr/bin/env python3

import datetime
import threading
import time

import arduino_interface
import cloud_db
import custom_queue
import ping


if __name__ == "__main__":
    timestamp_start = datetime.datetime.utcnow()

    # A queue with data to be written to the DB.
    data_queue = custom_queue.CustomQueue()

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
    cloud_uploader_thread = threading.Thread(
        target=cloud_db.cloud_uploader_loop,
        kwargs=dict(data_queue=data_queue)
    )
    cloud_uploader_thread.setDaemon(True)
    cloud_uploader_thread.start()

    time.sleep(10.0)
    while True:
        try:
            input("Press enter to show stats ")
            print()

            time_running = datetime.datetime.utcnow() - timestamp_start

            print("Elements currently in queue:", data_queue.qsize())
            print("Total elements put on the queue:", data_queue.total_elements_put())
            print("Time running:", time_running)
            print()
        except Exception as e:
            print(e)
