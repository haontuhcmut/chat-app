from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .middleware import register_middleware
from .auth.routes import auth_router
from .config import Config

version_prefix = Config.API_VER

app = FastAPI(
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
)

# Add middleware
register_middleware(app)


# Health check
@app.get(f"/{version_prefix}/health", tags=["Health"])
async def health():
    return JSONResponse(content={"message": "Welcome to Chat app!"}, status_code=200)

# Add routes
app.include_router(
    auth_router, prefix=f"/{version_prefix}/auth", tags=["Auth"]
)