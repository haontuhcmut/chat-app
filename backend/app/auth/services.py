from .schema import SignUpModel
from sqlmodel.ext.asyncio.session import AsyncSession
from ..core.model import User
from passlib.context import CryptContext
from sqlmodel import select, or_
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from ..utility.url_safe_token import encode_url_safe_token, decode_url_safe_token
from ..config import Config
from fastapi.templating import Jinja2Templates
from ..celery_task import send_email
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]  # /app/app
TEMPLATE_DIR = BASE_DIR / "html_template"

templates = Jinja2Templates(directory=TEMPLATE_DIR)
pwd_context = CryptContext(schemes=["sha512_crypt"], deprecated="auto")


def hashed_password(password: str) -> str:
    return pwd_context.hash(password)


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
                    raise HTTPException(status_code=400, detail="Username already exists")
                if existing_user.email == user_data.email:
                    raise HTTPException(status_code=400, detail="Email already exists")

            # Create new user
            data_dict = user_data.model_dump(exclude="password")
            new_user = User(**data_dict)
            new_user.hashed_password = hashed_password(password=user_data.password)
            new_user.role = "user"
            session.add(new_user)
            await session.flush()

            # Verify account
            token = encode_url_safe_token(dict(email=user_data.email))
            link = f"{Config.DOMAIN}/{Config.API_VER}/oauth/verify/{token}"
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
