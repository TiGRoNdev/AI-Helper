# SPDX-License-Identifier: LGPL-2.1-or-later


USER_SESSION_ACTIVE_TIME = 60 * 60 * 2  # 2 hours


class Err:
    @classmethod
    def __str__(cls):
        return cls.__name__


class DONT_ENOUGH_PARAMETERS(Err):
    msg = "Недостаточно параметров"


class UNSPECIFIED_ERROR(Err):
    msg = "Непредвиденная ошибка"


class USER_ALREADY_REGISTERED(Err):
    msg = "Данный пользователь уже зарегистрирован"


class USER_DOESNT_EXIST(Err):
    msg = "Данный пользователь не существует"


class USER_WRONG_CREDENTIALS(Err):
    msg = "Неправильно указаны данные для входа"


