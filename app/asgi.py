# SPDX-License-Identifier: LGPL-2.1-or-later


import os
import sys

''' Добавление пути на этапе исполнения '''
app_path = os.path.abspath('../app')
sys.path.append(app_path)

from app.handlers import on_shutdown
from app.views import routes

from aiohttp import web
import weakref


async def app_factory(argv=None):
    app = web.Application()  # create app
    app['websockets'] = weakref.WeakSet()

    app.add_routes(routes)  # add routes
    app.on_shutdown.append(on_shutdown)  # add shutdown handler

    return app
