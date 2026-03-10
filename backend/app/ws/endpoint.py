import json

from .manager import ConnectionManager
from fastapi import WebSocket, WebSocketDisconnect

from ..core.redis import redis_client

manager = ConnectionManager()


async def websocket_handler(ws: WebSocket):
    sid = ws.query_params.get("sid")
    if not sid:
        await ws.close(code=1008)
        return

    user_id = await redis_client.get(f"ws_session:{sid}")  # set from api session_id
    if user_id is None:
        await ws.close(code=1008)
        return

    await redis_client.delete(f"ws_session:{sid}")

    key = f"user:{user_id}"
    await manager.connect(key, ws)

    # set online
    added = await redis_client.sadd("online-users", user_id)

    # broadcast presence
    if added:
        await redis_client.publish(
            "broadcast",
            json.dumps(
                {
                    "key": "*",
                    "data": {
                        "type": "presence",
                        "_id": user_id,
                        "status": "online",
                    },
                }
            ),
        )

    try:
        while True:
            await ws.receive()
    except WebSocketDisconnect:
        await manager.disconnect(key, ws)

        if key not in manager.connections:
            await redis_client.srem("online-users", user_id)

            await redis_client.publish(
                "broadcast",
                json.dumps(
                    {
                        "key": "*",
                        "data": {
                            "type": "presence",
                            "_id": user_id,
                            "status": "offline",
                        },
                    }
                ),
            )
