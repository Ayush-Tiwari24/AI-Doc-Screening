"""
Seed script — creates the OFFICER001 demo user in the users table.
Run from the backend/ directory with:
    .venv\Scripts\python.exe seed.py
"""
import asyncio
import uuid
from passlib.context import CryptContext
from sqlalchemy import select, text
from db.session import engine, async_session_factory
from db.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed():
    # 1. Make sure tables exist
    async with engine.connect() as conn:
        try:
            await conn.execute(text("SELECT 1 FROM users LIMIT 1"))
            print("✓ users table exists")
        except Exception:
            print("✗ users table not found — run migrations first")
            return

    async with async_session_factory() as session:
        # Check if officer already exists
        result = await session.execute(
            select(User).where(User.badge_id == "OFFICER001")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"✓ OFFICER001 already exists (id={existing.id}, role={existing.role})")
            return

        # Create demo officer
        user = User(
            id=uuid.uuid4(),
            name="Demo Officer",
            badge_id="OFFICER001",
            role="OFFICER",
            checkpoint_id=None,
            password_hash=pwd_context.hash("Demo@123"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"✓ Created OFFICER001 (id={user.id})")

        # Also create an ADMIN user
        admin = User(
            id=uuid.uuid4(),
            name="Admin User",
            badge_id="ADMIN001",
            role="ADMIN",
            checkpoint_id=None,
            password_hash=pwd_context.hash("Admin@123"),
        )
        session.add(admin)
        await session.commit()
        print("✓ Created ADMIN001 (password: Admin@123)")


if __name__ == "__main__":
    asyncio.run(seed())
