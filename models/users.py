from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import false, text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from db.db import Base


chat_users = Table(
    'chat_users',
    Base.metadata,
    Column('chat_id', ForeignKey('chat.id', ondelete="CASCADE"), primary_key=True),
    Column('user_id', ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
)


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

    chats = relationship(
        "Chat",
        secondary=chat_users,
        back_populates="participants"
    )

    messages = relationship(
        "Message",
        foreign_keys="[Message.user_id]",
        back_populates="user"
    )



class Chat(Base):
    __tablename__ = "chat"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(ForeignKey("users.id", ondelete="CASCADE"))
    receiver_id = Column(ForeignKey("users.id", ondelete="CASCADE"))
    # messages = Column(String, nullable=True)

    participants = relationship(
        "User",
        secondary=chat_users,
        back_populates="chats"
    )

    messages = relationship(
        "Message",
        foreign_keys="[Message.chat_id]",
        back_populates="chat"
    )


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True) 
    message = Column(String, nullable=True) 
    chat_id = Column(ForeignKey("chat.id", ondelete="CASCADE")) 
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE")) 
    read = Column(Boolean, server_default=false())

    chat = relationship(
        "Chat",
        back_populates="messages"
    )

    user = relationship(
        "User",
        back_populates="messages"
    )
