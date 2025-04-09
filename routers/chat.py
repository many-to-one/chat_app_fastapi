import json
from typing import Annotated
from fastapi import APIRouter, status, Depends, Response, WebSocket, WebSocketDisconnect, Query, WebSocketException, Cookie
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from schemas.users import UserBase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import func, update, or_

from db.db import get_db
from models.users import Chat, Message, chat_users
from schemas.auth import TokenResponse, UserCreateForm, UserLoginForm
from schemas.chat import ChatBase, MessageBase
from security.security import get_current_user_with_cookies, get_password_hash, oauth2_scheme, get_current_user
from orm.orm import OrmService


router = APIRouter(tags=["Chat"], prefix="/chat")


@router.get("/all_chats", status_code=status.HTTP_200_OK, response_model=list[ChatBase])
async def all_chats(
    db: AsyncSession = Depends(get_db),
    # current_user: UserBase = Depends(get_current_user),
    # current_user: UserBase = Depends(get_current_user_with_cookies),
):
    result = await db.execute(
        select(Chat).options(selectinload(Chat.messages))  # Eagerly load the messages
    )
    chat_list = result.scalars().all()

    return [chat.model_dump() for chat in [ChatBase.from_orm(chat) for chat in chat_list]]


@router.get("/get_chat", status_code=status.HTTP_200_OK, response_model=list[ChatBase])
async def get_chat(
    sender_id: int,
    receiver_id: int,
    count: int,
    db: AsyncSession = Depends(get_db)
):
    __orm = OrmService(db)

    # Make message read=True by receiver
    await db.execute(
        update(Message)
        .where(Message.user_id == receiver_id)
        .values(read = True)
    )
    await db.commit()

    # Get chat conversation
    result = await db.execute(
    select(Chat)
    .filter(
        or_(
            (Chat.sender_id == sender_id) & (Chat.receiver_id == receiver_id),
            (Chat.sender_id == receiver_id) & (Chat.receiver_id == sender_id)
        )
    )
    .options(selectinload(Chat.messages))
)
    chat_list = result.scalars().all()

    for chat in chat_list:
        # print('##################### CHAT ID ####################', chat.id, count)
        if chat.messages:
            chat.messages = sorted(chat.messages, key=lambda msg: msg.id, reverse=True)[:count]  # Get last 100 messages

    return [ChatBase.from_orm(chat) for chat in chat_list]




# The last message of the chat
@router.get("/get_last_mess", status_code=status.HTTP_200_OK, response_model=list[ChatBase])
async def get_chat(
    sender_id: int,
    receiver_id: int,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
    select(Chat)
    .filter(
        or_(
            (Chat.sender_id == sender_id) & (Chat.receiver_id == receiver_id),
            (Chat.sender_id == receiver_id) & (Chat.receiver_id == sender_id)
        )
    )
    .options(selectinload(Chat.messages))  # Eagerly load 'messages'
)
    chat_list = result.scalars().all()

    # Extract the last message for each chat
    for chat in chat_list:
        if chat.messages:
            chat.messages = sorted(chat.messages, key=lambda msg: msg.id, reverse=True)[:1]
            chat.unread_count = 0
            for message in chat.messages:
                if message.read == False:
                    chat.unread_count += 1
        else:
            chat.messages = []
            chat.unread_count = 0
            chat.read = False


    # print(' ############## UNREAD COUNT ############## ', chat.unread_count)


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
        # Ensure this is a dictionary, not a list
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, chat_id: int):
        await websocket.accept()
        self.active_connections[chat_id] = websocket
        print('************* WEBSOCCET IS CONNECTED ***************')

    async def disconnect(self, websocket: WebSocket):
        user_id = next((uid for uid, ws in self.active_connections.items() if ws == websocket), None)
        if user_id:
            del self.active_connections[user_id]

    async def is_user_online(self, user_id: str) -> bool:
        return user_id in self.active_connections

    async def send_personal_message(self, message: str, websocket: WebSocket):
        if message.startswith == 'chat_onopen':
            await websocket.send_text(message)
        if message.startswith == 'chat_onclose':
            await websocket.send_text(message)
        else:
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

    def get_connection(self, user_id: int) -> WebSocket | None:
        return self.active_connections.get(user_id)
    


manager = ConnectionManager()



@router.websocket("/ws/{client_id}/{sender_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    sender_id: int, 
    client_id: int,
    token: str,
    # current_user: UserBase = Depends(get_current_user_with_cookies),
    # current_user: UserBase = Depends(get_current_user),
    # token: str = Depends(oauth2_scheme),
    # db: AsyncSession = Depends(get_db)
):

    await websocket.accept()
    while True:
    
        current_user = get_current_user_with_cookies(token)

        if not current_user:
            print(' *********** no current_user *********** ')
        #     await websocket.close(code=1008)  # Policy violation or unauthorized
        #     return
        await websocket.accept()

        print(' *********** current_user *********** ', current_user, token)
    

    # Validate token and authenticate user
    # if token:
    #     # print(' *********** token *********** ', token)
    #     current_user = await get_current_user(token, db)

    #     if current_user:
    #         print(' *********** CONNECT CURRENT USER ID *********** ', current_user.id)
    #         await manager.connect(websocket, current_user.id)
    #         message_data = {
    #                 "is active": current_user.id,
    #                 "sender_id": sender_id, 
    #                 "client_id": client_id,
    #             }
    #         await manager.broadcast(json.dumps(message_data))

    #         while True:
    #             data = await websocket.receive_json()
    #             print('SENDED DATA:', data, "Type:", type(data))

    # else:
    #     print(' *********** ERROR *********** ', websocket)
    #     websocket.close()
    
