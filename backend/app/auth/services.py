from sqlalchemy.util import deprecated

from backend.app.auth.schema import SignUpModel
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.model import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["sha512_crypt"], deprecated="auto")

def hashed_password(password: str) -> str:
    return pwd_context.hash(password)

class AuthServices:
    async def signup(self, user_data: SignUpModel, session: AsyncSession):
        data_dict = user_data.model_dump(exclude="password")
        new_user = User(**data_dict)
        new_user.hashed_password = hashed_password(password=user_data.password)
