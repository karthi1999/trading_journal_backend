from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_by_id(db: AsyncSession, user_id: str) -> User | None:
    return await db.get(User, user_id)


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_email_or_username(db: AsyncSession, email: str, username: str) -> User | None:
    result = await db.execute(
        select(User).where(or_(User.email == email, User.username == username))
    )
    return result.scalars().first()


async def create(db: AsyncSession, *, email: str, username: str, password_hash: str) -> User:
    user = User(email=email, username=username, password_hash=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
