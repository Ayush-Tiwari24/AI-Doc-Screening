import asyncio
from sqlalchemy import text
from db.session import engine

async def check():
    async with engine.connect() as c:
        try:
            r = await c.execute(text("SELECT badge_id, role FROM users LIMIT 5"))
            rows = r.fetchall()
            if rows:
                print("Users found:")
                for row in rows:
                    print(f"  badge_id={row[0]}, role={row[1]}")
            else:
                print("NO users in DB — will seed")
        except Exception as e:
            print(f"Table error: {e}")

asyncio.run(check())
