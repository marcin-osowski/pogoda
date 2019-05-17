#!/usr/bin/env python3

import bottle

import config
import app

config.DEV_MODE=False

bottle.run(
    app.app,
    server='paste',
    host=config.PROD_HTTP_HOST,
    port=config.PROD_HTTP_PORT,
    debug=config.DEV_MODE,
    reloader=config.DEV_MODE,
)

