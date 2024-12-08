from pydantic import BaseModel, EmailStr

class UserCreateForm(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLoginForm(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    id: int
    username: str
    access_token: str
    refresh_token: str


class ChangePasswordForm(BaseModel):
    email: EmailStr
    old_password: str
    new_password: str