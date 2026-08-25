"""
Live screening-session WebSocket.

Redis pub/sub bridges:
Celery worker -> Redis -> FastAPI -> browser
"""

import json
import uuid

import redis.asyncio as redis_async

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from config import settings
from services.status_events import (
    session_channel,
)


router = APIRouter()


@router.websocket(
    "/ws/sessions/{session_id}"
)
async def session_websocket(
    websocket: WebSocket,
    session_id: uuid.UUID,
):
    await websocket.accept()

    redis_client = (
        redis_async.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    )

    pubsub = redis_client.pubsub()

    channel = session_channel(
        str(session_id)
    )

    try:
        await pubsub.subscribe(
            channel
        )

        await websocket.send_json(
            {
                "type": "connected",
                "session_id": str(
                    session_id
                ),
            }
        )

        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if message is None:
                continue

            raw_data = message.get(
                "data"
            )

            try:
                payload = json.loads(
                    raw_data
                )

            except (
                TypeError,
                json.JSONDecodeError,
            ):
                payload = {
                    "type": "message",
                    "session_id": str(
                        session_id
                    ),
                    "data": raw_data,
                }

            await websocket.send_json(
                payload
            )

    except WebSocketDisconnect:
        pass

    finally:
        await pubsub.unsubscribe(
            channel
        )

        await pubsub.close()

        await redis_client.close()