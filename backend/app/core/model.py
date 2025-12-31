from sqlmodel import SQLModel, Field, Column
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import DateTime, func


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(default=None, unique=True, index=True)
    username: str = Field(default=None, unique=True)
    first_name: str = Field(default=None, max_length=32)
    last_name: str = Field(default=None, max_length=32)
    hashed_password: str = Field(default=None, exclude=True)
    is_verified: bool = Field(default=False)
    role: str = Field(default="user", max_length=16, nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )
    )
