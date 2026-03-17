import logging

logger = logging.getLogger(__name__)


class WSHandler:
    def __init__(self, manager, redis_store):
        self.manager = manager
        self.redis_store = redis_store

    async def connect(self, websocket, client_id: str):
        await self.manager.connect(client_id, websocket)
        await self.manager.broadcast(
            {"type": "presence", "client_id": client_id, "status": "online"}
        )

        conn_id = await self.redis_store.add_connection(client_id)

        if await self.redis_store.count(client_id) == 1:
            logger.info(f"[ONLINE] client_id {client_id}")
        return conn_id

    async def disconnect(self, websocket, client_id: str, conn_id: str):
        await self.manager.disconnect(client_id, websocket)

        await self.manager.broadcast(
            {
                "type": "presence",
                "client_id": client_id,
                "status": "offline",
            }
        )

        await self.redis_store.remove_connection(client_id, conn_id)

        if await self.redis_store.count(client_id) == 0:
            logger.info(f"[DISCONNECT] client_id {client_id} disconnected")
