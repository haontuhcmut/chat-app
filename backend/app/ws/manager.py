from fastapi import WebSocket
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, key: str, ws: WebSocket):
        await ws.accept()
        self.connections[key].add(ws)
        users, sockets = self._stats()
        logging.info(
            f"[WS CONNECT] user={key} "
            f"socket_id={id(ws)} "
            f"from={ws.client.host}:{ws.client.port if ws.client else None} "
            f"users={users} sockets={sockets}"
        )

    async def disconnect(self, key: str, ws: WebSocket):
        self.connections[key].discard(ws)
        if not self.connections[key]:
            del self.connections[key]
        users, sockets = self._stats()
        logging.info(
            f"[WS DISCONNECT] user={key} "
            f"socket_id={id(ws)} "
            f"users={users} sockets={sockets}"
        )


    async def send(self, key: str, data: dict):
        for ws in list(self.connections.get(key, [])):
            await ws.send_json(data)

    def _stats(self):
        total_users = len(self.connections)
        total_sockets = sum(len(v) for v in self.connections.values())
        return total_users, total_sockets
