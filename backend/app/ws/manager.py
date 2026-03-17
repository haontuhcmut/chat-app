from collections import defaultdict

from starlette.websockets import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id].add(websocket)

    async def disconnect(self, client_id: str, websocket: WebSocket):
        self.active_connections[client_id].discard(websocket)

        if not self.active_connections[client_id]:
            del self.active_connections[client_id]

    async def broadcast(self, message: dict):
        for conns in self.active_connections.values():
            for ws in conns:
                await ws.send_json(message)
