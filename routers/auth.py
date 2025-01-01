from fastapi import APIRouter, status, Depends, Response, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


from db.db import get_db
from models.users import User
from schemas.auth import TokenResponse, UserCreateForm, ChangePasswordForm
from schemas.users import UserBase
from security.security import get_new_access_token, get_password_hash, get_current_user, oauth2_scheme
from orm.orm import OrmService


router = APIRouter(tags=["Auth"], prefix="/auth")


@router.post("/sing_up", status_code=status.HTTP_201_CREATED, response_model=UserCreateForm)
async def sign_up(
        user_form: UserCreateForm, # = Depends(UserCreateForm), 
        db: AsyncSession = Depends(get_db)
    ):
    print('user_form', user_form)
    hashed_password = get_password_hash(user_form.password)
    user_data = user_form.dict() 
    user_data['password'] = hashed_password

    __orm = OrmService(db)
#    new_user = await __orm.create(model=User, form=user_data)

    try:
        new_user = await __orm.create(model=User, form=user_data)
        return new_user
    except IntegrityError as e:
        # Handle the case where the email already exists
        if "ix_users_email" in str(e):  # This checks if the error is related to the unique constraint
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The email address is already registered."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred."
            )

    return new_user


@router.post("/login", status_code=status.HTTP_200_OK, response_model=TokenResponse)
async def login(
        response: Response,
        user_form: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db), 
    ):
    
    __orm = OrmService(db)
    login_user = await __orm.login(form=user_form)
    return login_user


@router.get("/refresh_token", status_code=status.HTTP_200_OK, response_model=TokenResponse)
async def refresh_token(
        refresh_token: str,
        # db: AsyncSession = Depends(get_db), 
    ):
    
    new_access_token = get_new_access_token(refresh_token)

    return new_access_token


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
        response: Response,
        db: AsyncSession = Depends(get_db), 
        current_user: UserBase = Depends(get_current_user)
    ):
    
    current_user.is_active = False
    current_user.access_token = None
    await db.commit() 
    await db.refresh(current_user)
    return {
            'message': 'User has been loged out',
            'user_message': 'Poprawne wylogowanie'
        }


@router.post("/chanage_password", status_code=status.HTTP_201_CREATED)
async def chanage_password(
        response: Response,
        user_form: ChangePasswordForm = Depends(ChangePasswordForm),
        # token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db), 
        current_user: UserBase = Depends(get_current_user)
    ):

    hashed_password = get_password_hash(user_form.new_password)
    user = current_user #await get_current_user(token=token, db=db)

    if user_form.old_password != user.password:
        user.password = hashed_password
        await db.commit()

        return {
            'message': 'The password has been changed',
            'user_message': 'Hasło zostało zmienione'
        }
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
