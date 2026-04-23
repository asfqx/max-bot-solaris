from datetime import datetime
from uuid import UUID
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.model import User


class UserRepository:
    
    @staticmethod
    async def add(
        user: User,
        session: AsyncSession,
    ) -> User:
        
        session.add(user)
        await session.commit()
        
        return user

    @staticmethod
    async def get_by_chat_id(
        chat_id: int,
        session: AsyncSession,
    ) -> User | None:
        
        result = await session.execute(select(User).where(User.chat_id == chat_id))
        
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_uuid(
        user_uuid: UUID,
        session: AsyncSession, 
    ) -> User | None:
        
        result = await session.execute(select(User).where(User.uuid == user_uuid))
        
        return result.scalar_one_or_none()

    @staticmethod
    async def list_due(
        due_before: datetime, 
        session: AsyncSession,
        limit: int = 100,
    ) -> Sequence[User]:
        
        result = await session.execute(
            select(User)
            .where(User.next_reminder_at <= due_before)
            .order_by(User.next_reminder_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def delete(
        user: User,
        session: AsyncSession, 
    ) -> None:
        
        await session.delete(user)
        await session.commit()
        
