import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlmodel import SQLModel

from infra.config.container import Container
from infra.config.settings import Settings


@pytest.fixture(scope="session")
def settings():
    s = Settings()
    # Allow override for tests
    test_db = os.getenv("TEST_DATABASE_URL")
    if test_db:
        s.database_url = test_db
    elif "postgres:5432" in s.database_url and not os.environ.get("DATABASE_URL"):
        # Tentamos localhost, se falhar, SQLite.
        # Aqui apenas preparamos a URL. O engine será criado depois.
        s.database_url = s.database_url.replace("postgres:5432", "localhost:5432")

    return s


@pytest.fixture(scope="session")
def container(settings):
    c = Container()
    c.settings.override(settings)
    return c


@pytest.fixture
async def engine(settings):
    # Using function scope for engine to avoid loop mismatch issues in tests
    url = settings.database_url

    try:
        engine = create_async_engine(url, echo=False)
        # Test connection
        async with engine.connect() as conn:
            await conn.execute(select(1))
    except Exception:
        # Fallback to SQLite if Postgres is unavailable
        url = "sqlite+aiosqlite:///:memory:"
        engine = create_async_engine(url, echo=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_llm_service():
    mock = MagicMock()
    # Correctly mock async methods
    mock.generate_script = AsyncMock(
        return_value={
            "title": "Test Video",
            "hook": "Test hook",
            "body": "Test body",
            "call_to_action": "Test CTA",
        }
    )
    mock.generate_text = AsyncMock(return_value="Test text")
    return mock


@pytest.fixture
def mock_audio_service():
    mock = MagicMock()
    mock.generate_audio = AsyncMock(return_value=b"test_audio_bytes")
    return mock


@pytest.fixture
def mock_storage_service():
    mock = MagicMock()
    mock.upload_file = AsyncMock(return_value="https://example.com/test.mp3")
    return mock
