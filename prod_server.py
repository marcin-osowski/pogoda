#!/usr/bin/env python
import gevent.monkey
gevent.monkey.patch_all()

import bottle
import config
import app

config.DEV_MODE=False

bottle.run(
    app.app,
    server='gevent',
    host=config.HTTP_HOST,
    port=config.HTTP_PORT,
    debug=config.DEV_MODE,
    reloader=config.DEV_MODE,
)

