from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from models.users import Chat, Message
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
    # Add other origins as needed
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
        print('************* WEBSOCCET IS CONNECTED ***************')

    def disconnect(self, websocket: WebSocket):
        user_id = next((uid for uid, ws in self.active_connections.items() if ws == websocket), None)
        if user_id:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
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



@app.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    # sender_id: int, 
    # receiver_id: int,
    client_id: int,
    db: AsyncSession = Depends(get_db)
):

    await manager.connect(websocket, client_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()  # Expecting JSON with sender, receiver, and message
            sender_id = data["sender_id"]
            receiver_id = data["receiver_id"]
            message = data["message"]

            result = await db.execute(
                select(Chat)
                .filter(Chat.sender_id == sender_id, Chat.receiver_id == receiver_id)
                .options(selectinload(Chat.chat_messages))  # Eager load chat messages
            )
            obj = result.scalars().first()

            if obj is None:
                 # Save message in the database
                chat_form = {
                    "sender_id": sender_id,
                    "receiver_id": receiver_id,
                    "chat_messages": [Message(message=message)]
                }
                __orm = OrmService(db)
                new_chat = await __orm.create(model=Chat, form=chat_form)
                obj = new_chat

            # else:
            #     if obj and obj.chat_messages:
            #         for message in obj.chat_messages:
            #             await manager.send_personal_message(f"New message from Client #{sender_id}: {message.message}", websocket)


            # Notify the sender
            await manager.send_personal_message(f"Message sent to Client #{receiver_id}", websocket)

            # Send message to the receiver if connected
            receiver_ws = manager.get_connection(receiver_id)
            if receiver_ws:
                await manager.send_personal_message(f"New message from Client #{sender_id}: {message}", receiver_ws)

            else:
                # Optionally handle offline messaging
                mess = await manager.send_personal_message(f"Client #{receiver_id} is offline. Message saved.", websocket)
                new_message = Message(message=message, chat_id=obj.id)
                db.add(new_message)
                await db.commit()
                await db.refresh(new_message)

            # Broadcast message to everyone (optional)
            await manager.broadcast(f"Client #{sender_id} to #{receiver_id}: {message}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{obj.id} left the chat")



# @app.websocket("/ws/{client_id}")
# async def websocket_endpoint(websocket: WebSocket, client_id: int):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await manager.send_personal_message(f"You wrote: {data}", websocket)
#             await manager.broadcast(f"Client #{client_id} says: {data}")
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast(f"Client #{client_id} left the chat")