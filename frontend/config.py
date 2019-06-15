# Site location
SITE_LATITUDE=53.794847
SITE_LONGITUDE=20.437800

# Database settings.
GCP_CREDENTIALS="./gcp-credentials.json"
GCP_PROJECT="pogoda-240600"

# GCP kinds for sensor data.
GCP_TEMP_KIND="wczasowa:ground_level:reading:temperature"
GCP_HMDT_KIND="wczasowa:ground_level:reading:humidity"
GCP_PRES_KIND="wczasowa:ground_level:reading:pressure"
GCP_PM25_KIND="wczasowa:ground_level:reading:pm_25_env"
GCP_WND_SPEED_KIND="wczasowa:roof_level:reading:wind_speed"
GCP_WND_DIR_KIND="wczasowa:roof_level:reading:wind_direction"
GCP_RAIN_MM_KIND="wczasowa:roof_level:reading:total_rain_mm"

# GCP kinds for connection status data.
GCP_INTERNET_LATENCY="connection:internet_latency"
GCP_DB_LATENCY="connection:cloud_db_write_latency"
GCP_DB_SUCCESS_RATE="connection:cloud_db_write_success_rate"
GCP_ARDUINO_BPS="connection:arduino_comm_bps"

# Names of monitored loggers
MONITORED_LOGGERS={
    "ground_level": ("wczasowa:ground_level:", "Ground level"),
    "roof_level": ("wczasowa:roof_level:", "Roof level"),
}

# Web server settings.
PROD_HTTP_HOST='127.0.0.1'
PROD_HTTP_PORT=8092

DEV_HTTP_HOST='127.0.0.1'
DEV_HTTP_PORT=8080
