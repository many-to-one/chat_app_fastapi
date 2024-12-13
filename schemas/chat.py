from pydantic import BaseModel
from typing import Optional

class MessageBase(BaseModel):
    message: str
    chat_id: int
    user_id: Optional[int]
    read: bool

    class Config:
        from_attributes = True

class ChatBase(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    messages: list[MessageBase]

    class Config:
        from_attributes = True
    