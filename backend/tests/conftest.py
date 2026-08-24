import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from config import settings
from db.models import Base
from db.session import get_session
from main import app


TEST_DATABASE_URL = (
    settings.database_url.rsplit("/", 1)[0]
    + "/docscreening_test"
)


# Important:
# - NullPool prevents connections from being reused between tests.
# - statement_cache_size=0 disables asyncpg prepared-statement caching.
# This is important because the test suite drops and recreates the
# PostgreSQL schema, including the user_role enum.
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={
        "statement_cache_size": 0,
    },
)

TestSessionFactory = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(
    scope="function",
    autouse=True,
)
async def setup_test_db():

    # Create a fresh schema for every test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Remove the schema after every test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Make sure all connections are closed
    await test_engine.dispose()


async def override_get_session():
    async with TestSessionFactory() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def unique_badge_id():
    return f"BADGE-{uuid.uuid4().hex[:8]}"