from pydantic import BaseModel

class MessageBase(BaseModel):
    message: str

    class Config:
        from_attributes = True

class ChatBase(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    chat_messages: list[MessageBase]

    class Config:
        from_attributes = True
    