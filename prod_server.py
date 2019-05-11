#!/usr/bin/env python

import bottle

import config
import app

config.DEV_MODE=False

bottle.run(
    app.app,
    server='paste',
    host=config.HTTP_HOST,
    port=config.HTTP_PORT,
    debug=config.DEV_MODE,
    reloader=config.DEV_MODE,
)

