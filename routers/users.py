from fastapi import APIRouter, status, Depends, Response
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from cachetools import TTLCache

from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from models.users import User
from schemas.auth import TokenResponse, UserCreateForm, UserLoginForm
from schemas.users import UserBase
from security.security import get_current_user, get_password_hash, oauth2_scheme
from orm.orm import OrmService


router = APIRouter(tags=["Users"], prefix="/users")

# In-memory cache with a max size of 1 and TTL of 10 minutes (600 seconds)
cache = TTLCache(maxsize=1, ttl=600)

@router.get("/user_profile/{id}", status_code=status.HTTP_200_OK, response_model=UserBase)
async def user_profile(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: UserBase = Depends(get_current_user)
    ):

    __orm = OrmService(db)

    return await __orm.get(id=user_id, model=User, name='user_profile')


@router.get("/all_users", status_code=status.HTTP_200_OK, response_model=list[UserBase])
async def all_users(
    db: AsyncSession = Depends(get_db),
    current_user: UserBase = Depends(get_current_user)
):
    # Check if users are cached
    if "all_users" in cache:
        # print('//////////////// ALL USERS IN CASHE /////////////////')
        return cache["all_users"]

    else:

        # Fetch data from database if not in cache
        __orm = OrmService(db)
        all_users = await __orm.all(model=User, name='all_users')

        # Cache the data
        cache["all_users"] = all_users
        # print('//////////////// ALL USERS NOT IN CASHE /////////////////')

        return all_users