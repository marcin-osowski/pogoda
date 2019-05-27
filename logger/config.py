COMM_PORT="/dev/ttyUSB0"
LOGGER_INTERVAL_SEC=120
NAME_TRANSLATION={
    "Humidity": "humidity",
    "Temperature": "temperature",
    "Water level": "water_level",
    "Pressure": "pressure",

    "PM 1.0 standard": "pm_10_std",
    "PM 2.5 standard": "pm_25_std",
    "PM 10.0 standard": "pm_100_std",
    "PM 1.0 environmental": "pm_10_env",
    "PM 2.5 environmental": "pm_25_env",
    "PM 10.0 environmental": "pm_100_env",

    "Particles > 0.3um / 0.1L air": "particles_03",
    "Particles > 0.5um / 0.1L air": "particles_05",
    "Particles > 1.0um / 0.1L air": "particles_10",
    "Particles > 2.5um / 0.1L air": "particles_25",
    "Particles > 5.0um / 0.1L air": "particles_50",
    "Particles > 10.0 um / 0.1L air": "particles_100",
}

# Limits RAM usage in case of DB unreachability.
# Approximate limit.
MAX_QUEUE_SIZE=1024*1024

# Database settings.
GCP_CREDENTIALS="./gcp-credentials.json"
GCP_PROJECT="pogoda-240600"
GCP_READING_PREFIX="reading:"
