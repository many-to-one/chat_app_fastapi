# import datetime
from datetime import datetime, timedelta, timezone
from db.db import get_db
from fastapi import HTTPException, status
from jose import JWTError, jwt
# from .settings import settings
from passlib.context import CryptContext
# from fastapi.security import HTTPBearer
from fastapi.security.oauth2 import OAuth2PasswordBearer
from fastapi import Depends
from models.users import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from schemas.auth import TokenResponse

from dotenv import load_dotenv
import os

load_dotenv()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# auth_scheme = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_password_hash(password):
    return pwd_context.hash(password)


# Verify Hash Password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)



# Create Access & Refresh Token
async def get_tokens_pair(db, id):

    payload = {'id': id}
    access_token = await create_access_token(payload)
    refresh_token = await create_refresh_token(payload)

    print('***************** access_token *****************', access_token)

    result = await db.execute(select(User).filter(User.id == id))
    user = result.scalar_one_or_none()
    user.access_token = access_token
    user.refresh_token = refresh_token
    db.add(user)
    await db.commit()
    await db.refresh(user)

    response = TokenResponse(
        id=user.id,
        username=user.username,
        photo=user.photo,
        email=user.email,
        access_token=access_token,
        refresh_token=refresh_token,
    )

    return response


# Create New Access Token via Refresh Token
async def get_new_access_token(refresh_token: str):

    try:
        payload = jwt.decode(refresh_token, os.getenv("SECRET_KEY"), algorithm=os.getenv("algorithm"))

        return await create_access_token(payload)
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token.",
            headers={"WWW-Authenticate": "Bearer"}
        )


# Create Access Token
async def create_access_token(data: dict):

    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=5) #1600
    payload.update({"exp": expire}) 

    return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm=os.getenv("algorithm"))


# Create Refresh Token
async def create_refresh_token(data: dict):

    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    payload.update({"exp": expire}) 

    return jwt.encode(data, os.getenv("SECRET_KEY"), os.getenv("algorithm"))


# Get Payload Of Token
async def get_token_payload(token: str)-> dict:
    try:
        return jwt.decode(token, os.getenv("SECRET_KEY"), [os.getenv("algorithm")])

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    

# token: str = Depends(oauth2_scheme) for Swagger Authorize
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db))-> User:

    user = await get_token_payload(token)
    user_id = user.get('id')
    result = await db.execute(select(User).filter(User.id == user_id))
    current_user = result.scalar_one_or_none()
    
    return current_user


async def check_admin(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):

    user = await get_token_payload(token)
    user_id = user.get('id')
    result = await db.execute(select(User).filter(User.id == user_id))
    current_user = result.scalar_one_or_none()
    if current_user.is_admin != True:
        raise HTTPException(status_code=403, detail="Admin role required")