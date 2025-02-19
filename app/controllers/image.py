# SPDX-License-Identifier: LGPL-2.1-or-later


from app import USER_WRONG_CREDENTIALS
from app.logic.auth import authorize
from app.models import Image
from app.db import get_session


async def upload_image(msg, ws=None, args=None):
    """ Загрузить изображение """
    user, session_key = await authorize(args.user_id[0], args.session[0])
    if not user:
        return await ws.send_str(f"[ERROR][{USER_WRONG_CREDENTIALS()}] {USER_WRONG_CREDENTIALS.msg}")

    async with get_session() as session:
        image = Image(path=args.data[0])

        if args.chat_message:
            image.chat_message = args.chat_message[0]

        session.add(image)

    return await ws.send_json({
        'image': image.id,
        'session': session_key
    })
