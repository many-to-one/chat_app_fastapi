from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    id: int
    username: str
    photo: Optional[str] = None
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime