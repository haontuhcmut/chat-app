import json

from .manager import ConnectionManager
from ..core.redis import redis_client

async def redis_listener(manager: ConnectionManager):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("broadcast")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        payload = json.loads(message["data"])
        key = payload["key"]
        data = payload["data"]

        await manager.send(key, data)
