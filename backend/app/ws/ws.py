from fastapi import APIRouter, WebSocket
import jwt
from starlette.websockets import WebSocketDisconnect

from .handler import WSHandler
from .manager import ConnectionManager
from .redis_store import RedisConnectionStore
from ..config import Config
from ..core.redis import redis_client

ws_router = APIRouter()
manager = ConnectionManager()
redis_store = RedisConnectionStore(redis_client)
handler = WSHandler(manager, redis_store)


@ws_router.websocket("/")
async def ws_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[f"{Config.ALGORITHM}"])
    client_id = payload.get("user_id")

    if not client_id:
        await websocket.close(code=1008)

    conn_id = await handler.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()

            await manager.send_message(client_id, data)
    except WebSocketDisconnect:
        await handler.disconnect(websocket, client_id, conn_id)
