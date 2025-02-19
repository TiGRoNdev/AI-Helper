# SPDX-License-Identifier: LGPL-2.1-or-later


from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint


class User(SQLModel, table=True):
    __tablename__ = "aihelper_user"
    __table_args__ = (UniqueConstraint("phone_number"),)

    id: int | None = Field(None, primary_key=True)
    password: str
    phone_number: str
    fernet_key: str | None
    session_key: str | None  # sha1(id|ip|user-agent)


class Chat(SQLModel, table=True):
    __tablename__ = "aihelper_chat"

    id: int | None = Field(None, primary_key=True)
    title: str
    creation_time: datetime

    # keys
    user_id: int = Field(index=True, foreign_key="aihelper_user.id")


class ChatMessage(SQLModel, table=True):
    __tablename__ = "aihelper_chat_message"

    id: int | None = Field(None, primary_key=True)
    role: str
    content: str | None = Field(default=None)
    dt: datetime

    # keys
    chat: int = Field(index=True, foreign_key="aihelper_chat.id")

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content
        }


class Image(SQLModel, table=True):
    __tablename__ = "aihelper_image"

    id: int | None = Field(None, primary_key=True)
    path: str | None

    # keys
    chat_message: int | None = Field(default=None, index=True, foreign_key="aihelper_chat_message.id")
