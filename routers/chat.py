from fastapi import APIRouter, status, Depends, Response, WebSocket, WebSocketDisconnect
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from db.db import get_db
from models.users import Chat
from schemas.auth import TokenResponse, UserCreateForm, UserLoginForm
from schemas.chat import ChatBase
from security.security import get_password_hash, oauth2_scheme
from orm.orm import OrmService


router = APIRouter(tags=["Chat"], prefix="/chat")


@router.get("/new_chat", status_code=status.HTTP_200_OK, response_model=ChatBase)
async def create_chat(
    sender_id: int,
    receiver_id: int,
    db: AsyncSession = Depends(get_db)
):
    chat_form = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message": "Hello",
    }
    __orm = OrmService(db)

    return await __orm.create(model=Chat, form=chat_form)


@router.get("/get_chat", status_code=status.HTTP_200_OK, response_model=list[ChatBase])
async def get_chat(
    sender_id: int,
    receiver_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
                select(Chat)
                .filter(
                    Chat.sender_id == sender_id, 
                    Chat.receiver_id == receiver_id,
                )
                .options(
                    selectinload(Chat.chat_messages)  # Eager load the related messages
                )
            )
    chat_list = result.scalars().all() 

    return [ChatBase.from_orm(chat) for chat in chat_list]


@router.get("/delete_all_chats", status_code=status.HTTP_200_OK)
async def delete_all_chats(db: AsyncSession = Depends(get_db)):

    __orm = OrmService(db)

    all_chats = await __orm.all(model=Chat, name='get_all_chats')
    for chat in all_chats:
        await __orm.delete(id=chat.id, model=Chat, name='delete_single_chat')

    return {
        'message': 'All chats has been deleted'
    }



class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


# @router.websocket("/ws/{client_id}")
# async def websocket_endpoint(
#     websocket: WebSocket, 
#     client_id: int, 
#     sender_id: int,
#     receiver_id: int,
#     db: AsyncSession = Depends(get_db)
# ):
    
#     __orm = OrmService(db)
#     await manager.connect(websocket)
#     try:
#         while True:
#             # Receive message from client
#             data = await websocket.receive_json()  # Expecting JSON with sender, receiver, and message
#             sender_id = data["sender_id"]
#             receiver_id = data["receiver_id"]
#             message = data["message"]

#             # Save message in the database
#             chat_form = {
#                 "sender_id": sender_id,
#                 "receiver_id": receiver_id,
#                 "message": message,
#             }

            
#             new_chat = await __orm.create(model=Chat, form=chat_form)

#             # Notify the sender
#             await manager.send_personal_message(f"Message sent to Client #{receiver_id}", websocket)

#             # Send message to the receiver if connected
#             receiver_ws = manager.get_connection(receiver_id)
#             if receiver_ws:
#                 await manager.send_personal_message(f"New message from Client #{sender_id}: {message}", receiver_ws)
#             else:
#                 # Optionally handle offline messaging
#                 await manager.send_personal_message(f"Client #{receiver_id} is offline. Message saved.", websocket)

#             # Broadcast message to everyone (optional)
#             await manager.broadcast(f"Client #{sender_id} to #{receiver_id}: {message}")

#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast(f"Client #{client_id} left the chat")