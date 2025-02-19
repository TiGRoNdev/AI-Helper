# SPDX-License-Identifier: LGPL-2.1-or-later

import aiohttp
from aiohttp import web
import logging
import traceback
import argparse
import json

from wsframework.commands import WebSocketCommand

logger = logging.getLogger('aiohttp.server')


class WS_MSG_TYPE:
    TEXT = 0
    JSON = 1
    BINARY = 2


class WsJsonStatus:
    OK = 200
    ERROR = 500
    USER_ERROR = 400


class WSEndpointMetaclass(type):
    @staticmethod
    def _get_needed_attr(key, attrs, bases):
        attr = attrs.get(key, None)

        if not attr:
            for base in bases:
                attr_tmp = getattr(base, key, None)
                if attr_tmp is not None:
                    return attr_tmp

        return attr

    def __new__(mcs, clsname, bases, old_attrs):
        ws_com_attrs = {
            attr: (v.handler, v.parser.set_prog(attr) if v.parser else None, v.required_args)
            for attr, v in old_attrs.items()
            if isinstance(v, WebSocketCommand)
        }

        help_commands = "\n\t".join([
            f"- {attr}: {v.description}"
            for attr, v in old_attrs.items()
            if isinstance(v, WebSocketCommand)
        ])

        attrs = {
            'get': mcs._get_needed_attr('get', old_attrs, bases),
            'handler': mcs.__handler(
                ws_com_attrs,
                f'Доступные команды:\n\t{help_commands}'
            )
        }

        return super(WSEndpointMetaclass, mcs).__new__(mcs, clsname, bases, attrs)

    @staticmethod
    def __handler(func_map, help_msg):
        class _MetaNamespace:
            pass

        async def wrapper(self, msg, ws=None, binary=False):
            """
            Обработчик входных сообщений WebSocket

                Осуществляет парсинг входной строки и создает объект _MetaNamespace с атрибутами равными
                заданным аргументам командной строки(WebSocket)
            """
            try:
                namespace = None
                message = None

                if not binary:
                    msg_type = WS_MSG_TYPE.TEXT
                    try:
                        message = json.loads(msg.data)
                        msg_type = WS_MSG_TYPE.JSON
                    except json.JSONDecodeError:
                        message = msg.data.strip().split()

                    if msg_type == WS_MSG_TYPE.TEXT:
                        namespace = _MetaNamespace()
                        # help
                        if message[0] in ('help', 'h', '--help'):
                            return await ws.send_str(help_msg)

                        func, arg_parser, required_args = func_map[message[0]]

                        arg_parser.parse_args(message[1:], namespace=namespace)
                        if namespace.help:
                            return await ws.send_str(arg_parser.format_help())

                        # check for required attrs
                        if len(set(required_args) - set([key for key in vars(namespace).keys() if getattr(namespace, key) is not None])) > 0:
                            return await ws.send_str(f"[ERROR][DONT_ENOUGH_PARAMETERS] You need to specify {', '.join(required_args)}.")

                    else:
                        if message['rpc'].lower() == 'help':
                            return await ws.send_json({
                                'code': WsJsonStatus.OK,
                                'body': help_msg
                            })
                        func, _, _ = func_map[message['rpc']]
                else:
                    msg_type = WS_MSG_TYPE.BINARY
                    func, _, _ = func_map['__binary']

                return await func(
                    message['body'] if msg_type == WS_MSG_TYPE.JSON else msg.data,
                    ws=ws,
                    args=namespace
                )
            except (argparse.ArgumentError, Exception):
                logger.error(f"Ошибка:\n{traceback.format_exc()}")
                return await ws.send_str(f"ERROR")

        return wrapper


class Meta(WSEndpointMetaclass, type(web.View)):
    pass


class WSEndpoint(web.View, metaclass=Meta):
    async def get(self):
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        self.request.app['websockets'].add(ws)
        try:
            async for msg in ws:
                logger.info(f"[WS-LOG]\t[INCOMING MSG]\t{msg.data}")
                try:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        if msg.data == 'close':
                            await ws.close()
                        else:
                            await self.handler(msg, ws=ws)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f'ws connection closed with exception {ws.exception()}')
                    elif msg.type == aiohttp.WSMsgType.BINARY:
                        await self.handler(msg, ws=ws, binary=True)
                except Exception as err:
                    logger.error(f"Ошибка:\n{traceback.format_exc()}")
                    return await ws.send_str(f"[ERROR][UNSPECIFIED_ERROR] Непредвиденная ошибка")
        finally:
            self.request.app['websockets'].discard(ws)

        logger.info('websocket connection closed by client.')
        return ws
