from fastapi import APIRouter, status, Depends, Response
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from models.users import User
from schemas.auth import TokenResponse, UserCreateForm, UserLoginForm
from schemas.users import UserBase
from security.security import get_current_user, get_password_hash, oauth2_scheme
from orm.orm import OrmService


router = APIRouter(tags=["Users"], prefix="/users")

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

    __orm = OrmService(db)
    return await __orm.all(model=User, name='all_users')
