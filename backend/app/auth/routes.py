from typing import Annotated
import uuid
from datetime import datetime

from fastapi import APIRouter, Response, HTTPException
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from .dependency import get_current_user, RefreshTokenBearer

from .schema import SignUpModel, UserModel, TokenModel
from .services import AuthServices, create_access_token
from ..config import Config
from ..core.dependency import SessionDep
from ..core.redis import add_jti_blocklist


auth_services = AuthServices()
auth_router = APIRouter()


@auth_router.post("/signup", status_code=200)
async def signup(user: SignUpModel, session: SessionDep):
    new_user = await auth_services.signup(user, session)
    return new_user


@auth_router.get("/verify/{token}")
async def verify_user_token(token: str, session: SessionDep):
    token_url_safe = await auth_services.verify_account(token, session)
    return token_url_safe


@auth_router.post("/signin")
async def signin(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    session: SessionDep,
):
    access_token, refresh_token = await auth_services.signin(form_data, session)
    # HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,  # Prevents JavaScript from accessing the cookie (security enhancement)
        secure=False,  # Ensure the cookie is only sent over HTTPS (essential in production)
        samesite="strict",  # Controls cross-site cookie behavior
        max_age=3600 * 24 * 7,  # Cookie expiration time in seconds
    )
    return TokenModel(access_token=access_token)


@auth_router.get("/me")
async def get_current_user(user: Annotated[UserModel, Depends(get_current_user)]):
    return user


@auth_router.post("/signout")
async def signout(
    response: Response,
    refresh_token_payload: Annotated[dict, Depends(RefreshTokenBearer())],
):
    print(refresh_token_payload)
    jti = refresh_token_payload["jti"]
    await add_jti_blocklist(jti)
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=False,
        samesite="strict",
    )
    return JSONResponse(status_code=200, content={"message": "Successfully logged out"})


@auth_router.post("/refresh")
async def token_refresh(
    refresh_token_payload: Annotated[dict, Depends(RefreshTokenBearer())],
):
    exp_time = refresh_token_payload.get("exp")
    if datetime.fromtimestamp(exp_time) > datetime.now():
        new_token = create_access_token(
            data_dict={
                "email": refresh_token_payload.get("email"),
                "username": refresh_token_payload.get("username"),
                "role": refresh_token_payload.get("role"),
                "jti": str(uuid.uuid4()),
            },
            refresh=False,
        )
        return TokenModel(access_token=new_token)
    raise HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )