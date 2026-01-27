import uuid
from .schema import SignUpModel
from sqlmodel.ext.asyncio.session import AsyncSession
from ..core.model import User
from sqlmodel import select, or_
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from ..utility.url_safe_token import encode_url_safe_token, decode_url_safe_token
from ..config import Config
from fastapi.templating import Jinja2Templates
from ..celery_task import send_email
from pathlib import Path
from datetime import datetime, timedelta, timezone
import jwt
from typing import Any
from pwdlib import PasswordHash

BASE_DIR = Path(__file__).resolve().parents[1]  # /app/app
TEMPLATE_DIR = BASE_DIR / "html_template"

templates = Jinja2Templates(directory=TEMPLATE_DIR)
password_hasher = PasswordHash.recommended()


def get_hashed_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password)


def create_token(
    data_dict: dict,
    expires_delta: timedelta | None = None,
    refresh: bool | None = False,
):
    to_encode = data_dict.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "refresh": refresh})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt


class AuthServices:
    async def signup(self, user_data: SignUpModel, session: AsyncSession):
        try:
            # Check email and username exist
            stmt = select(User).where(
                or_(User.email == user_data.email, User.username == user_data.username)
            )
            result = await session.exec(stmt)
            existing_user = result.first()
            if existing_user:
                if existing_user.username == user_data.username:
                    raise HTTPException(
                        status_code=400, detail="Username already exists"
                    )
                if existing_user.email == user_data.email:
                    raise HTTPException(status_code=400, detail="Email already exists")

            # Create new user
            data_dict = user_data.model_dump(exclude="password")
            new_user = User(**data_dict)
            new_user.hashed_password = get_hashed_password(password=user_data.password)
            new_user.role = "user"
            session.add(new_user)
            await session.flush()

            # Verify account
            token = encode_url_safe_token(dict(email=user_data.email))
            link = f"{Config.DOMAIN}/verify?token={token}"
            html_content = templates.get_template("verify_email.html").render(
                {"action_url": link, "first_name": user_data.first_name}
            )

            emails = [user_data.email]
            subject = "Verify your email"
            send_email.delay(emails, subject, html_content)

            await session.commit()

            return JSONResponse(
                content={"message": "Email verification sent"},
                status_code=200,
            )
        except HTTPException:
            await session.rollback()
            raise

    async def verify_account(self, token: str, session: AsyncSession):
        token_data = decode_url_safe_token(token)
        user_email = token_data.get("email")
        stmt = select(User).where(User.email == user_email)
        result = await session.exec(stmt)
        user_current = result.first()
        if not user_current:
            raise HTTPException(status_code=404, detail="User not found")
        else:
            user_current.is_verified = True
            session.add(user_current)
            await session.commit()
            return JSONResponse(
                content={"message": "User verified"},
                status_code=200,
            )

    async def signin(
        self,
        form_data: Any,
        session: AsyncSession,
    ):
        email = form_data.username
        password = form_data.password
        stmt = select(User).where(User.email == email)
        result = await session.exec(stmt)
        user = result.first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token = create_token(
            data_dict={
                "user_id": str(user.id),
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "jti": str(uuid.uuid4()),
            },
            expires_delta=timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES),
            refresh=False,
        )

        # Create refresh token
        user.jti_current_token = str(uuid.uuid4())
        session.add(user)
        await session.commit()

        refresh_token = create_token(
            data_dict={
                "user_id": str(user.id),
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "jti":  user.jti_current_token,
            },
            expires_delta=timedelta(days=Config.REFRESH_TOKEN_EXPIRE_DAYS),
            refresh=True,
        )

        return access_token, refresh_token
