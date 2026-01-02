from ..config import Config
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker


database_url = Config.DATABASE_URL
engine = create_async_engine(database_url, future=True)

AsyncSessionLocal = sessionmaker(
   bind=engine,
   class_=AsyncSession,
   expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

        await session.rollback()
