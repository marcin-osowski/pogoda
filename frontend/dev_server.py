#!/usr/bin/env python3

import bottle

import config
import app

config.DEV_MODE=True

bottle.run(
    app.app,
    server='paste',
    host=config.DEV_HTTP_HOST,
    port=config.DEV_HTTP_PORT,
    debug=config.DEV_MODE,
    reloader=config.DEV_MODE,
)

