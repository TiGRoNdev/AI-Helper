# SPDX-License-Identifier: LGPL-2.1-or-later


from sqlalchemy import select

from app import DONT_ENOUGH_PARAMETERS, USER_WRONG_CREDENTIALS
from app.logic.auth import start_session, is_there_user, authorize, hash_password, verify_password
from app.db import get_session
from app.models import User
from app.controllers import LOGIN, LOGOUT, REGISTER


async def register(msg, ws=None, args=None):
    """ Регистрация пользователя в системе """

    if not args.phone:
        return await ws.send_str(f"[ERROR][{DONT_ENOUGH_PARAMETERS()}] {DONT_ENOUGH_PARAMETERS.msg}")

    user, status, _ = await is_there_user(args.phone[0])
    if user:
        return await ws.send_str(status)

    async with get_session() as session:
        user = User(
            phone_number=args.phone[0],
            password=hash_password(args.password[0])
        )
        session.add(user)

    session_key = await start_session(user.id)

    return await ws.send_json({
        "action": REGISTER,
        "payload": {
            'id': user.id,
            'session': session_key
        }
    })


async def login(msg, ws=None, args=None):
    """ Логин пользователя в систему по паролю """

    if not args.phone:
        return await ws.send_str(f"[ERROR][{DONT_ENOUGH_PARAMETERS()}] {DONT_ENOUGH_PARAMETERS.msg}")

    user, status, user_candidate = await is_there_user(args.phone[0])
    if not user:
        return await ws.send_str(status)

    verified = verify_password(user_candidate.password, args.password[0])
    if not verified:
        return await ws.send_str(f"[ERROR][{USER_WRONG_CREDENTIALS}] {USER_WRONG_CREDENTIALS.msg}")

    session = await start_session(user_candidate.id)

    return await ws.send_json({
        "action": LOGIN,
        "payload": {
            'id': user_candidate.id,
            'session': session
        }
    })


async def logout(msg, ws=None, args=None):
    """ Выход пользователя из системы """
    user, _ = await authorize(args.user_id[0], args.session[0])
    if not user:
        return await ws.send_str(f"[ERROR][{USER_WRONG_CREDENTIALS()}] {USER_WRONG_CREDENTIALS.msg}")

    async with get_session() as session:
        user = (await session.execute(select(User).filter_by(id=int(user.id)))).scalar_one()
        user.fernet_key = None
        user.session_key = None

    return await ws.send_json({
        "action": LOGOUT,
        "payload": {
            'id': user.id
        }
    })

