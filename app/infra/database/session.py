"""Database session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)


class DatabaseSessionManager:
    """Manager for database engine and session factory."""

    def __init__(self, db_url: str):
        self._engine = create_async_engine(db_url, pool_pre_ping=True, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provides a session context.
        Note: Commit/Rollback is the responsibility of the repository
        to avoid conflicts with operations like 'refresh' and multiple commits.
        """
        async with self._session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    async def close(self):
        """Close the engine."""
        if self._engine:
            await self._engine.dispose()
