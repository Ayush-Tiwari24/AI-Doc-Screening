"""
Redis pub/sub helpers for live screening-session updates.
"""

import json

import redis

from config import settings


def session_channel(
    session_id: str,
) -> str:
    return (
        f"screening-session:{session_id}"
    )


def publish_session_event(
    session_id: str,
    event_type: str,
    data: dict,
):
    """
    Publish an event from Celery/FastAPI to Redis.
    """

    client = redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    payload = {
        "type": event_type,
        "session_id": session_id,
        "data": data,
    }

    client.publish(
        session_channel(session_id),
        json.dumps(
            payload,
            default=str,
        ),
    )

    client.close()