#!/usr/bin/env python3

from datetime import datetime, timezone
import threading
import time

import arduino_interface
import cloud_db
import custom_queue
import db_buffer
import logger_stats
import ping


if __name__ == "__main__":
    timestamp_start = datetime.now(timezone.utc)

    # A queue with data to be written to the DB.
    data_queue = custom_queue.CustomQueue()

    # Logger statistics.
    logger_statistics = logger_stats.LoggerStatistics()

    def thread_kickoff(target, **kwargs):
        kwargs["data_queue"] = data_queue
        thread = threading.Thread(
            target=target,
            kwargs=kwargs,
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
        logger_statistics=logger_statistics,
    )

    # Start the SQLite DB buffer thread.
    sqlite_buffer_thread = thread_kickoff(
        target=db_buffer.sqlite_buffer_loop,
    )

    # Start the statistics writer thread.
    logger_statistics_thread = thread_kickoff(
        target=logger_statistics.statistics_writer_thread,
    )

    # Show the "user menu".
    time.sleep(10.0)
    while True:
        try:
            input("Press enter to show stats ")
            print()

            # Gather data.
            elements_in_queue = data_queue.qsize()
            new_elements_put = data_queue.total_new_elements_put()
            sqlite_elements = db_buffer.count_sqlite_elements()
            time_running = datetime.now(timezone.utc) - timestamp_start

            # Show it
            print("Elements currently in the queue:", elements_in_queue)
            print("Total new elements put in the queue:", new_elements_put)
            print("Elements in the SQLite DB:", sqlite_elements)
            print("Program running (time):", time_running)
            print()

        except Exception as e:
            print("Problem in the user menu")
            print(e)
