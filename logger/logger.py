#!/usr/bin/env python3

from datetime import datetime, timezone
import threading
import time

import arduino_interface
import cloud_db
import custom_queue
import db_buffer
import ping


if __name__ == "__main__":
    timestamp_start = datetime.now(timezone.utc)

    # A queue with data to be written to the DB.
    data_queue = custom_queue.CustomQueue()

    def thread_kickoff(target):
        thread = threading.Thread(
            target=func,
            kwargs=dict(data_queue=data_queue)
        )
        thread.setDaemon(True)
        thread.start()

    # Start a thread to scrape Arduino data.
    arduino_scraper_thread = thread_kickoff(
        target=arduino_interface.arduino_scraper_loop,
    )

    # Start a thread to scrape connection quality data.
    conn_quality_scraper_thread = thread_kickoff(
        target=ping.conn_quality_scraper_loop,
    )

    # Start popping items from the readings queue
    # and inserting them into the DB.
    cloud_uploader_thread = thread_kickoff(
        target=cloud_db.cloud_uploader_loop,
    )

    # Start the SQLite DB buffer thread.
    sqlite_buffer_thread = thread_kickoff(
        target=db_buffer.sqlite_buffer_loop,
    )

    # Show the "user menu".
    time.sleep(10.0)
    while True:
        try:
            input("Press enter to show stats ")
            print()

            time_running = datetime.now(timezone.utc) - timestamp_start

            print("Elements currently in the queue:", data_queue.qsize())
            print("Total elements put in the queue:", data_queue.total_elements_put())
            print("Time running:", time_running)
            print()
        except Exception as e:
            print(e)
