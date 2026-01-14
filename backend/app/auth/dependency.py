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


class TokenBearer:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    async def __call__(self, token: Annotated[str, Depends(oauth2_scheme)]):
        try:
            payload = jwt.decode(
                token, Config.SECRET_KEY, algorithms=[f"{Config.ALGORITHM}"]
            )
            await self.verify_token(payload)
            return payload

        except InvalidTokenError:
            raise self.credentials_exception

    async def verify_token(self, payload: dict) -> None:
        pass


class AccessTokenBearer(TokenBearer):
    async def verify_token(self, payload: dict) -> None:
        if payload.get("refresh"):
            raise HTTPException(
                status_code=401,
                detail="Access token is required.",
                headers={"WWW-Authenticate": "Bearer"},
            )


class RefreshTokenBearer(TokenBearer):
    async def verify_token(self, payload: dict) -> None:
        if not payload.get("refresh"):
            raise HTTPException(
                status_code=401,
                detail="Refresh token is required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        jti = payload.get("jti")
        if jti is None or await token_in_jti_blocklist(jti=jti):
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
