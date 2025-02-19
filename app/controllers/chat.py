# SPDX-License-Identifier: LGPL-2.1-or-later


from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from app import USER_WRONG_CREDENTIALS
from app.logic.auth import authorize
from app.logic.model import get_title_from_message, streaming_response_generator
from app.models import Chat, Image, ChatMessage
from app.db import get_session


async def send_message(msg, ws=None, args=None):
    """ Отправить сообщение в чат с вложениями """
    user, session_key = await authorize(args.user_id[0], args.session[0])
    if not user:
        return await ws.send_str(f"[ERROR][{USER_WRONG_CREDENTIALS()}] {USER_WRONG_CREDENTIALS.msg}")

    dt = datetime.now()

    async with get_session() as session:
        chat = None
        if args.id:
            try:
                chat = (await session.execute(select(Chat).filter_by(id=int(args.id[0])))).scalar_one()
            except NoResultFound:
                pass

        if not chat:
            title = await get_title_from_message(" ".join(args.text))
            chat = Chat(
                title=title,
                creation_time=dt,
                user_id=int(user.id)
            )
            session.add(chat)
            await session.flush()

        message = ChatMessage(
            content=" ".join(args.text),
            role='user',
            dt=dt,
            chat=chat.id
        )
        session.add(message)
        await session.flush()

        if args.images:
            images = (await session.execute(select(Image).where(Image.id.in_([int(i) for i in args.images])))).scalars()
            for img in images:
                img.chat_message = message.id
                session.add(img)
            await session.flush()

    async with get_session() as session:
        messages = (await session.execute(select(ChatMessage)
                                          .where(ChatMessage.chat == int(chat.id))
                                          .order_by(ChatMessage.dt))).scalars()
        prepared_messages = []
        for msg in messages:
            msg_images = (await session.execute(select(Image).where(Image.chat_message == int(msg.id)))).scalars()
            if msg_images:
                prepared_messages.append({
                    **msg.to_dict(),
                    "images": [img.path for img in msg_images]
                })
            else:
                prepared_messages.append(msg.to_dict())

    assistant_message = ""
    async for response_chunk in streaming_response_generator(prepared_messages):
        await ws.send_json({
            'message_chunk': {
                "message": response_chunk,
                "done": False
            },
            'session': session_key,
            'chat': chat.id
        })
        assistant_message += response_chunk

    async with get_session() as session:
        message = ChatMessage(
            content=assistant_message,
            role='assistant',
            dt=datetime.now(),
            chat=chat.id
        )
        session.add(message)

    return await ws.send_json({
        'message_chunk': {
            "message": None,
            "done": True
        },
        'session': session_key,
        'chat': chat.id
    })