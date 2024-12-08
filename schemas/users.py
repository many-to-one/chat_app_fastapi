from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime