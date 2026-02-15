from .manager import ConnectionManager
from fastapi import WebSocket, WebSocketDisconnect

from ..core.redis import redis_client

manager = ConnectionManager()


async def websocket_handler(ws: WebSocket):
    sid = ws.query_params.get("sid")
    if not sid:
        await ws.close(code=1008)
        return

    user_id = await redis_client.get(f"ws_session:{sid}")
    if user_id is None:
        await ws.close(code=1008)
        return

    await redis_client.delete(f"ws_session:{sid}")

    key = f"user:{user_id}"
    await manager.connect(key, ws)

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(key, ws)


