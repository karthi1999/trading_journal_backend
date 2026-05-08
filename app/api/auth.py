from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db import prisma
from app.schemas.auth import RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> TokenResponse:
    existing = await prisma.user.find_first(
        where={"OR": [{"email": payload.email}, {"username": payload.username}]}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already in use",
        )
    user = await prisma.user.create(
        data={
            "email": payload.email,
            "username": payload.username,
            "passwordHash": hash_password(payload.password),
        }
    )
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    # OAuth2PasswordRequestForm uses `username` field; we accept email there.
    user = await prisma.user.find_unique(where={"email": form.username})
    if not user or not verify_password(form.password, user.passwordHash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_user)) -> UserResponse:
    return UserResponse.from_model(user)
