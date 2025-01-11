from datetime import datetime
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from schemas.users import UserBase
from security.security import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from models.users import Chat, Message, chat_users
from orm.orm import OrmService
from routers import auth, users, chat
from db.db import get_db

import os

########## SECRETE KEY LOGIC ##########
# secret_key = os.urandom(32).hex()
# print(f"SECRET_KEY = '{secret_key}'")
#######################################

app = FastAPI()

origins = [
    "http://localhost:8081",  # React app running locally
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(chat.router)



class ConnectionManager:
    def __init__(self):
        # Ensure this is a dictionary, not a list
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, chat_id: int):
        await websocket.accept()
        self.active_connections[chat_id] = websocket
        # self.active_connections[user_id] = websocket
        print('************* WEBSOCCET IS CONNECTED ***************')

    def disconnect(self, websocket: WebSocket):
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


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('chat.html', {"request": request})



@app.websocket("/ws/{client_id}/{sender_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    sender_id: int, 
    client_id: int,
    token: str,
    db: AsyncSession = Depends(get_db)
):

    # Validate token and authenticate user
    if token:
        current_user = await get_current_user(token, db)

        if current_user:
            print(' *********** WEBSOCKET INDEX CURRENT USER ID *********** ', current_user.id)
            await users_manager.connect(websocket, current_user.id)

        else:
            await websocket.close(code=1008)  # Close WebSocket if unauthorized
            await users_manager.broadcast("401 Unauthorized")
            return
    else:
        await websocket.close(code=1008)  # Close WebSocket if no token
        await users_manager.broadcast("No token")
        return
    # await manager.connect(websocket, sender_id)

    try:
        while True:

            try:
                data = await websocket.receive_json()
                print('SENDED DATA:', data)

                # Broadcast "chat_onopen" message
                if data["message"] == "chat_onopen":
                    await manager.broadcast(f"chat_onopen {data['sender_id']} is active")
                    is_active = await manager.is_user_online(data['receiver_id'])
                    print(' ################ chat_onopen is_active ################ ', is_active)

                elif data["message"] == "receiver_active":
                    print(' ################ receiver_active ################ ', data)
                    # await manager.broadcast(f"is_active")

                # If use 'else' - will be send a message 'chat_onopen' or 'chat_onclose'
                # But if use 'elif...' will be send only real user's message
                elif data["message"] != "chat_onopen" and data["message"] != "chat_onclose":
                    sender_id = data["sender_id"]
                    receiver_id = data["receiver_id"]
                    is_active = await manager.is_user_online(receiver_id)
                    print(' ################ send is_active ################ ', is_active)
                    message = data["message"]

                    print(' ################ SENDED USER MESSAGE ################ ', message)

                    result = await db.execute(
                        select(Chat)
                        .join(chat_users)
                        .filter(chat_users.c.user_id.in_([sender_id, receiver_id]))
                        .group_by(Chat.id)
                        .having(func.count(chat_users.c.user_id) == 2)  # Ensure both users exist in the same chat
                        .options(selectinload(Chat.messages))
                    )
                    obj = result.scalars().first()

                    if obj is None:
                        # Save message in the database
                        chat_form = {
                            "sender_id": sender_id,
                            "receiver_id": receiver_id,
                            "messages": [Message(message=message, read=is_active)]
                        }
                        __orm = OrmService(db)
                        new_chat = await __orm.create(model=Chat, form=chat_form)
                        await db.execute(
                            chat_users.insert().values([
                                {"chat_id": new_chat.id, "user_id": sender_id},
                                {"chat_id": new_chat.id, "user_id": receiver_id}
                            ])
                        )
                        await db.commit()

                        obj = new_chat

                    else:
                        print(' ################ I"M HERE ################ ', message)
                        # Handle messaging
                        new_message = Message(
                            message=message, 
                            chat_id=obj.id,
                            user_id=sender_id,
                            read=is_active,
                            created_at=datetime.utcnow()
                            )
                        db.add(new_message)
                        await db.commit()
                        await db.refresh(new_message)

                    await manager.broadcast(f"Client #{sender_id} to #{receiver_id}: {message}, receiver_active: {is_active}")

            except WebSocketDisconnect:
                print(f"WebSocket client_id {client_id} disconnected.")
                manager.disconnect(websocket)
                break
            except Exception as e:
                print(f"Error in WebSocket: {e}")
                await websocket.close()
                break


    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{sender_id} left the chat")




from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.future import select
import json


class ConnectionUsersManager:
    def __init__(self):
        # Ensure this is a dictionary, not a list
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, chat_id: int):
        await websocket.accept()
        self.active_connections[chat_id] = websocket
        # self.active_connections[user_id] = websocket
        print('************* WEBSOCCET IS CONNECTED ***************')

    def disconnect(self, websocket: WebSocket):
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

users_manager = ConnectionUsersManager()

# All chats of user
@app.websocket("/ws/")
async def websocket_endpoint(
    websocket: WebSocket, 
    token: str, 
    db: AsyncSession = Depends(get_db),
):

    # Validate token and authenticate user
    if token:
        current_user = await get_current_user(token, db)

        if current_user:
            print(' *********** WEBSOCKET CURRENT USER ID *********** ', current_user.id)
            await users_manager.connect(websocket, current_user.id)

        else:
            await websocket.close(code=1008)  # Close WebSocket if unauthorized
            await users_manager.broadcast("401 Unauthorized")
            return
    else:
        await websocket.close(code=1008)  # Close WebSocket if no token
        await users_manager.broadcast("No token")
        return

    try:
        while True:
            # Wait for a message or event from the client
            data = await websocket.receive_json()  # Expecting JSON with sender, receiver, and message
            print(' ************** RECEIVED FOR INDEX DATA ************** ', data)
            await users_manager.broadcast(f"{data}")

    except WebSocketDisconnect:
        users_manager.disconnect(websocket)
        await users_manager.broadcast(json.dumps({
            "message": f"{current_user.id} left chats area"
        }))

    except Exception as e:
        print("WebSocket Error:", e)
        await websocket.close(code=1011)



# @app.websocket("/ws/")
# async def websocket_endpoint(
#     websocket: WebSocket, 
#     token: str, 
#     db: AsyncSession = Depends(get_db),
# ):

#     if token:
#         print(' *********** WEBSOCKET TOKEN 2 *********** ', token)
#         current_user = await get_current_user(token, db)

#         if current_user:
#             print(' *********** WEBSOCKET CURRENT USER ID *********** ', current_user.id)
#             await manager.connect(websocket, current_user.id)
#     else:
#         manager.disconnect(websocket)
#         await manager.broadcast(f"Unauthtorized")


#     try:
#         while True:
#             result = await db.execute(
#                 select(Message).
#                 where(Message.user_id == current_user.id)
#             )
#             obj = result.scalars().first()
#             print(' ********* USERS MESSAGES ********* ', obj)
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast(f"{current_user.id} left chats area")
