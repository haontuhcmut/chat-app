import asyncio
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import FastAPI, WebSocket

from .core.redis import redis_client
from .friends.routes import friend_router
from .conversations.routes import conv_router
from .messages.routes import message_router
from .middleware import register_middleware
from .auth.routes import auth_router
from .ws.endpoint import websocket_handler, manager
from .ws.redis_listener import redis_listener
from .ws.routes import ws_router
from .config import Config
from .core.logging import setup_logging
from fastapi_pagination import add_pagination

version_prefix = Config.API_VER

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_task  = asyncio.create_task(redis_listener(manager))
    yield
    redis_task.cancel()
    await redis_client.close()

app = FastAPI(
    lifespan=lifespan,
    title="Chat app backend",
    description="This is a backend service for a chat app.",
    version=f"{version_prefix}",
    contact={
        "name": "Hao Nguyen",
        "email": "nguyenminhhao1188@gmail.com",
        "url": "https://github.com/haontuhcmut/chat_app",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_url=f"/{Config.API_VER}/openapi.json",
    docs_url=f"/{Config.API_VER}/docs",
    redoc_url=f"/{Config.API_VER}/redoc",
)

# Add middleware
register_middleware(app)

# Health check
@app.get(f"/{version_prefix}/health", tags=["Health"])
async def health():
    return JSONResponse(content={"message": "Welcome to Chat app!"}, status_code=200)

@app.websocket(f"/{version_prefix}/ws")
async def ws_endpoint(ws: WebSocket):
    await websocket_handler(ws)

# Add routes
app.include_router(
    auth_router, prefix=f"/{version_prefix}/auth", tags=["Auth"]
)

app.include_router(friend_router, prefix=f"/{version_prefix}/friends", tags=["Friends"])
app.include_router(conv_router, prefix=f"/{version_prefix}/conversations", tags=["Conversations"])
app.include_router(message_router, prefix=f"/{version_prefix}/messages", tags=["Messages"])
app.include_router(ws_router, prefix=f"/{version_prefix}/auth_ws", tags=["Websockets"])


# Add pagination support
add_pagination(app)