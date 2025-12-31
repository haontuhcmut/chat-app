from backend.app.auth.schema import SignUpModel
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.model import User
from passlib.context import CryptContext
from sqlmodel import select
from fastapi.exceptions import HTTPException
from backend.app.utility.url_safe_token import encode_url_safe_token
from backend.app.config import Config
from fastapi.templating import Jinja2Templates



templates = Jinja2Templates(directory="backend/html_templates")

pwd_context = CryptContext(schemes=["sha512_crypt"], deprecated="auto")
def hashed_password(password: str) -> str:
    return pwd_context.hash(password)


class AuthServices:
    async def signup(self, user_data: SignUpModel, session: AsyncSession):
        #Check email and username exist
        stmt = select(User).where(User.email == user_data.email) | select(User).where(User.username == user_data.username)
        result = await session.exec(stmt)
        existing_user = result.first()
        if existing_user:
            if existing_user.username == user_data.username:
                raise HTTPException(status_code=400, detail="Username already exists")
            if existing_user.email == user_data.email:
                raise HTTPException(status_code=400, detail="Email already exists")

        #Create new user
        data_dict = user_data.model_dump(exclude="password")
        new_user = User(**data_dict)
        new_user.hashed_password = hashed_password(password=user_data.password)
        new_user.role = "user"
        session.add(new_user)
        await session.commit()

        #Verify account
        token = encode_url_safe_token(dict(email=user_data.email))
        link= f"{Config.DOMAIN}/{Config.API_VERSION}/oauth/verify/{token}"
        html_content = templates.get_template("verify_email.html").render(
            {"action_url": link, "first_name": user_data.first_name}
        )

        emails = [user_data.email]
        subject = "Verify your email"



