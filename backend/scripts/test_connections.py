import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import redis
from sqlalchemy import text

from db.session import engine
from storage.client import get_s3_client
from config import settings


async def test_postgres():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
    print("Postgres: OK")


def test_redis():
    r = redis.from_url(settings.redis_url)
    r.set("connection_test", "ok")
    assert r.get("connection_test") == b"ok"
    print("Redis: OK")


def test_minio():
    client = get_s3_client()
    buckets = client.list_buckets()
    bucket_names = [b["Name"] for b in buckets["Buckets"]]
    assert settings.minio_bucket in bucket_names
    print(f"MinIO: OK (bucket '{settings.minio_bucket}' found)")


async def main():
    await test_postgres()
    test_redis()
    test_minio()
    print("\nAll connections successful.")


if __name__ == "__main__":
    asyncio.run(main())