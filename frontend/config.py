# Database settings.
GCP_CREDENTIALS="./gcp-credentials.json"
GCP_PROJECT="pogoda-240600"

# GCP kinds for sensor data.
GCP_TEMP_KIND="wczasowa:ground_level:reading:temperature"
GCP_HMDT_KIND="wczasowa:ground_level:reading:humidity"
GCP_PRES_KIND="wczasowa:ground_level:reading:pressure"
GCP_PM25_KIND="wczasowa:ground_level:reading:pm_25_env"

# GCP kinds for latency data.
GCP_GROUND_INTERNET_LATENCY_KIND="wczasowa:ground_level:connection:internet_latency"
GCP_GROUND_DB_LATENCY_KIND="wczasowa:ground_level:connection:cloud_db_write_latency"
GCP_GROUND_DB_SUCCESS_RATE_KIND="wczasowa:ground_level:connection:cloud_db_write_success_rate"
GCP_GROUND_ARDUINO_BPS="wczasowa:ground_level:connection:arduino_comm_bps"

# Web server settings.
PROD_HTTP_HOST='127.0.0.1'
PROD_HTTP_PORT=8092

DEV_HTTP_HOST='127.0.0.1'
DEV_HTTP_PORT=8080
