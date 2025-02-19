# SPDX-License-Identifier: LGPL-2.1-or-later


from aiohttp import WSCloseCode


async def on_shutdown(app):
    """  Server shutdown signal  """
    for ws in set(app['websockets']):
        await ws.close(code=WSCloseCode.GOING_AWAY,
                       message='Server shutdown')

