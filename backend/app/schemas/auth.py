"""Authentication and role profile payloads."""
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field
from app.schemas.common import Role


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=32)
    emergency_contact: str | None = Field(default=None, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: str | None = None
    role: Role
    is_active: bool
    created_at: datetime | None = None


class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserPublic
