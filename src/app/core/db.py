from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from app.constants import POOL_RECYCLE, POOL_SIZE

from .settings import settings


class Base(DeclarativeBase, AsyncAttrs):

    uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        
        return cls.__name__.lower()


engine = create_async_engine(
    settings.database_url,
    pool_recycle=POOL_RECYCLE,
    pool_size=POOL_SIZE,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(bind=engine)
