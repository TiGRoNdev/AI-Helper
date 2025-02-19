# SPDX-License-Identifier: LGPL-2.1-or-later

from aiohttp import web
from wsframework import WSEndpoint, WebSocketCommand, CommandArgument

from app.controllers.lk import register, login, logout
from app.controllers.image import upload_image
from app.controllers.chat import send_message

routes = web.RouteTableDef()


@routes.view('/lk')
class LK(WSEndpoint):
    register = WebSocketCommand(
        register,
        "Регистрация пользователя в системе",
        phone=CommandArgument(['--phone'], help_text="Номер телефона"),
        password=CommandArgument(['--password'], required=True, help_text="Пароль юзверя"),
    )

    login = WebSocketCommand(
        login,
        "Логин пользователя в систему",
        phone=CommandArgument(['--phone'], help_text="Номер телефона"),
        password=CommandArgument(['--password'], required=True, help_text="Пароль юзверя"),
    )

    logout = WebSocketCommand(
        logout,
        "Логаут пользователя из системы",
        session=CommandArgument(['--session'], required=True, help_text="Ключ сессии пользователя"),
        user_id=CommandArgument(['--user_id'], required=True, help_text="ID пользователя")
    )


@routes.view('/image')
class Image(WSEndpoint):
    upload = WebSocketCommand(
        upload_image,
        "Загрузка картинки",
        data=CommandArgument(['--data'], required=True, help_text="Данные картинки в формате base64"),
        chat_message=CommandArgument(['--chat_message'], type_arg=int, help_text="ID чата"),
        session=CommandArgument(['--session'], required=True, help_text="Ключ сессии пользователя"),
        user_id=CommandArgument(['--user_id'], required=True, help_text="ID пользователя")
    )


@routes.view('/chat')
class Chat(WSEndpoint):
    send_message = WebSocketCommand(
        send_message,
        "Отправить сообщение в Chat",
        id=CommandArgument(['--id'], type_arg=int, help_text="ID чата"),
        text=CommandArgument(['--text'], help_text="Текст сообщения"),
        images=CommandArgument(['-img', '--images'], help_text="ID изображений для прикрепления"),
        session=CommandArgument(['--session'], required=True, help_text="Ключ сессии пользователя"),
        user_id=CommandArgument(['--user_id'], required=True, help_text="ID пользователя")
    )
