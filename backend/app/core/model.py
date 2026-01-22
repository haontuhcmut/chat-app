from sqlmodel import SQLModel, Field, Column, Relationship
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
    jti_current_token: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )
    )

    sent_friend_requests: list["FriendRequests"] = Relationship(
        back_populates="from_user",
        sa_relationship_kwargs={"foreign_keys": "[FriendRequests.from_user_id]"},
    )

    received_friend_requests: list["FriendRequests"] = Relationship(
        back_populates="to_user",
        sa_relationship_kwargs={"foreign_keys": "[FriendRequests.to_user_id]"},
    )
    friends_as_a: list["Friend"] = Relationship(
        back_populates="user_a_rel",
        sa_relationship_kwargs={"foreign_keys": "[Friend.user_a]"},
    )

    friends_as_b: list["Friend"] = Relationship(
        back_populates="user_b_rel",
        sa_relationship_kwargs={"foreign_keys": "[Friend.user_b]"},
    )
    messages: list["Message"] = Relationship(back_populates="user")


class FriendRequests(SQLModel, table=True):
    __tablename__ = "friend_requests"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    from_user_id: UUID = Field(default=None, foreign_key="user.id", nullable=False)
    to_user_id: UUID = Field(default=None, foreign_key="user.id", nullable=False)
    message: str = Field(default=None, nullable=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )
    )

    from_user: User | None = Relationship(
        back_populates="sent_friend_requests",
        sa_relationship_kwargs={"foreign_keys": "[FriendRequests.from_user_id]"},
    )

    to_user: User | None = Relationship(
        back_populates="received_friend_requests",
        sa_relationship_kwargs={"foreign_keys": "[FriendRequests.to_user_id]"},
    )


class Friend(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_a: UUID = Field(default=None, foreign_key="user.id", nullable=False)
    user_b: UUID = Field(default=None, foreign_key="user.id", nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )
    )

    user_a_rel: User | None = Relationship(
        back_populates="friends_as_a",
        sa_relationship_kwargs={"foreign_keys": "[Friend.user_a]"},
    )

    user_b_rel: User | None = Relationship(
        back_populates="friends_as_b",
        sa_relationship_kwargs={"foreign_keys": "[Friend.user_b]"},
    )


class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    sender_user_id: UUID = Field(default=None, foreign_key="user.id", nullable=False)
    content: str | None = Field(default=None, nullable=True)
    img_url: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )
    )

    user: User | None = Relationship(back_populates="messages")
