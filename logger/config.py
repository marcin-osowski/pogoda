# The port with Arduino data.
COMM_PORT="/dev/ttyUSB0"

# Interval for scraping the readings data.
LOGGER_INTERVAL_SEC=120

# Limits RAM usage in case of DB unreachability.
MAX_QUEUE_SIZE=256*1024

# Database settings.
GCP_CREDENTIALS="./gcp-credentials.json"
GCP_PROJECT="pogoda-240600"

# Database schema settings.

# The entity kind for a sensor reading is fully specified as:
#    instance_config.GCP_INSTANCE_NAME_PREFIX +
#    GCP_READING_PREFIX +
#    GCP_READING_NAME_TRANSLATION.value
GCP_READING_PREFIX="reading:"
GCP_READING_NAME_TRANSLATION={
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

# The entity kind for connection quality data is fully specified as:
#    instance_config.GCP_INSTANCE_NAME_PREFIX +
#    GCP_CONN_QUALITY_PREFIX +
#    "internet_latency"
GCP_CONN_QUALITY_PREFIX="connection:"
