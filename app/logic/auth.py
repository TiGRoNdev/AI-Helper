# SPDX-License-Identifier: LGPL-2.1-or-later


import time
import traceback
import logging

from cryptography.fernet import Fernet
import bcrypt

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from app.models import User
from app.db import get_session
from app import USER_ALREADY_REGISTERED, USER_DOESNT_EXIST, USER_SESSION_ACTIVE_TIME


SESSION_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7',
    'cache-control': 'no-cache',
    'dnt': '1',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
}


async def is_there_user(phone):
    async with get_session() as session:
        try:
            user = (await session.execute(select(User).filter_by(phone_number=phone))).scalar_one()
        except NoResultFound:
            user = None

    if user:
        return True, f"[ERROR][{USER_ALREADY_REGISTERED}] Пользователь уже существует", user

    return False, f"[ERROR][{USER_DOESNT_EXIST}] Пользователь не найден", user


async def start_session(user_id):
    fernet_key = Fernet.generate_key().decode()
    fernet = Fernet(fernet_key.encode())
    session_key = fernet.encrypt(f"{user_id}|{time.time() + USER_SESSION_ACTIVE_TIME}".encode()).decode()

    async with get_session() as session:
        user = (await session.execute(select(User).filter_by(id=int(user_id)))).scalar_one()
        user.fernet_key = fernet_key
        user.session_key = session_key

    return user.session_key


def _verify_user_session(user, session_key):
    if not user.fernet_key:
        return False

    try:
        fernet = Fernet(user.fernet_key.encode())
        session = fernet.decrypt(session_key.encode()).decode()
    except:
        logging.error(f"Ошибка:\n{traceback.format_exc()}")
        return False

    user_id, expire = session.split('|')
    return int(user_id) == user.id and float(expire) > time.time()


async def authorize(user_id, session_key):
    """
        Возвращает либо инстанс пользователя и ключ сессии при успешной авторизации, либо None
    """
    try:
        async with get_session() as session:
            try:
                user = (await session.execute(select(User).filter_by(id=int(user_id)))).scalar_one()
            except NoResultFound:
                user = None

            verified = _verify_user_session(user, session_key)
            if not user or not verified:
                return None, None

        return user, session_key
    except:
        logging.error(f"Ошибка:\n{traceback.format_exc()}")
        return None, None


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password.decode()


def verify_password(stored_password: str, provided_password: str) -> bool:
    return bcrypt.checkpw(provided_password.encode(), stored_password.encode())

