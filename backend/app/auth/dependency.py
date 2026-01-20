from fastapi import Request

import jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import HTTPException
from fastapi.params import Depends

from ..core.dependency import SessionDep
from .schema import UserModel
from ..config import Config
from ..core.model import User
from ..core.redis import token_in_jti_blocklist
from jwt.exceptions import InvalidTokenError
from typing import Annotated
from sqlmodel import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/{Config.API_VER}/auth/signin")


class AccessTokenBearer:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    async def __call__(self, token: Annotated[str, Depends(oauth2_scheme)]) -> dict:

        try:
            payload = jwt.decode(
                token, Config.SECRET_KEY, algorithms=[f"{Config.ALGORITHM}"]
            )
            if payload.get("refresh"):
                raise HTTPException(
                    status_code=401,
                    detail="Access token is required.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            jti = payload.get("jti")
            if jti is None or await token_in_jti_blocklist(jti):
                raise self.credentials_exception
            return payload
        except InvalidTokenError:
            raise self.credentials_exception


class RefreshTokenBearer:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    def __init__(self, cookies_name: str = "refresh_token"):
        self.cookies_name = cookies_name

    async def __call__(self, request: Request, session: SessionDep) -> dict:
        token = request.cookies.get(self.cookies_name)
        if not token:
            raise self.credentials_exception
        try:
            payload = jwt.decode(
                token, Config.SECRET_KEY, algorithms=[f"{Config.ALGORITHM}"]
            )

            if not payload.get("refresh"):
                raise HTTPException(
                    status_code=401,
                    detail="Refresh token is required.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            stmt = select(User).where(User.email == payload["email"])
            result = await session.exec(stmt)
            user = result.first()

            if not user:
                raise self.credentials_exception

            if str(payload.get("jti")) != str(user.jti_current_token):
                raise self.credentials_exception

            return payload
        except InvalidTokenError:
            raise self.credentials_exception


async def get_current_user(
    token_detail: Annotated[dict, Depends(AccessTokenBearer())], session: SessionDep
):
    email = token_detail["email"]
    stmt = select(User).where(User.email == email)
    result = await session.exec(stmt)
    user = result.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserModel(**user.model_dump())
