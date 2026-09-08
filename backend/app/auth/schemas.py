from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr = Field(..., description="Unique email address for registration")
    password: str = Field(..., min_length=8, max_length=128, description="Plaintext password (min 8 characters)")
    full_name: Optional[str] = Field(default=None, max_length=255, description="Full name of user")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Registered user email")
    password: str = Field(..., description="User password")


class UserAuthResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Seconds until expiration")
    user: UserAuthResponse


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
