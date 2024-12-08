from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import false, text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from db.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, server_default=false(), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    is_admin = Column(Boolean, server_default=false(), nullable=False)
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)

    sent_chats = relationship(
        "Chat",
        foreign_keys="[Chat.sender_id]",
        back_populates="sender"
    )
    received_chats = relationship(
        "Chat",
        foreign_keys="[Chat.receiver_id]",
        back_populates="receiver"
    )


class Chat(Base):
    __tablename__ = "chat"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(ForeignKey("users.id", ondelete="CASCADE"))
    receiver_id = Column(ForeignKey("users.id", ondelete="CASCADE"))
    message = Column(String, nullable=True)

    sender = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_chats"
    )
    receiver = relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_chats"
    )
    chat_messages = relationship(
        "Message",
        foreign_keys="[Message.chat_id]",
        back_populates="messages"
    )


class Message(Base):
    __tablename__ = "message"

    message = Column(String, primary_key=True, nullable=True)
    chat_id = Column(ForeignKey("chat.id", ondelete="CASCADE")) 

    messages = relationship(
        "Chat",
        foreign_keys=[chat_id],
        back_populates="chat_messages"
    )