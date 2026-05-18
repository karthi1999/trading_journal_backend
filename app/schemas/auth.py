from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    created_at: datetime

    @classmethod
    def from_model(cls, user) -> "UserResponse":
        return cls(
            id=user.id, email=user.email, username=user.username, created_at=user.created_at
        )
