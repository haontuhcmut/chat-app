from sqlmodel import SQLModel, Field, Column, Relationship
import enum
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import DateTime, func, Index, Enum


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(default=None, unique=True, index=True)
    username: str = Field(default=None, unique=True)
    first_name: str = Field(default=None, max_length=32)
    last_name: str = Field(default=None, max_length=32)
    avatar_url: str | None = Field(default=None, nullable=True)
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

    conversations: list["Conversation"] = Relationship(back_populates="user")
    conv_participants: list["ConvParticipant"] = Relationship(back_populates="user")


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


class ConvType(str, enum.Enum):
    direct = "direct"
    group = "group"


class Conversation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    type: ConvType = Field(
        sa_column=Column(Enum(ConvType), nullable=False)
    )
    last_message_id: UUID | None = Field(default=None, foreign_key="message.id")
    last_message_content: str | None = None
    last_message_sender_id: UUID | None = Field(default=None, foreign_key="user.id")
    last_message_at: datetime | None = Field(sa_column=Column(DateTime(timezone=True)))

    conv_participants: list["ConvParticipant"] = Relationship(
        back_populates="conversation"
    )
    group_conversation: "GroupConversation" = Relationship(
        back_populates="conversation"
    )

    user: User | None = Relationship(back_populates="conversations")


class ConvParticipant(SQLModel, table=True):
    __tablename__ = "conv_participant"

    conv_id: UUID = Field(foreign_key="conversation.id", primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    joined_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    conversation: Conversation | None = Relationship(back_populates="conv_participants")
    user: User | None = Relationship(back_populates="conv_participants")


class GroupConversation(SQLModel, table=True):
    __tablename__ = "group_conversation"
    conv_id: UUID = Field(
        default=None, foreign_key="conversation.id", nullable=False, primary_key=True
    )
    name: str = Field(default=None, nullable=False)
    created_by: UUID = Field(default=None, foreign_key="user.id", nullable=False)

    conversation: Conversation = Relationship(back_populates="group_conversation")


class ConvSeen(SQLModel, table=True):
    __tablename__ = "conv_seen"

    conv_id: UUID = Field(
        default=None, foreign_key="conversation.id", nullable=False, primary_key=True
    )
    user_id: UUID = Field(
        default=None, foreign_key="user.id", nullable=False, primary_key=True
    )
    seen_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class ConvUnread(SQLModel, table=True):
    __tablename__ = "conv_unread"

    user_id: UUID = Field(
        default=None, foreign_key="user.id", nullable=False, primary_key=True
    )
    conv_id: UUID = Field(
        default=None, foreign_key="conversation.id", nullable=False, primary_key=True
    )
    unread_count: int | None = Field(default=int(0), nullable=False)


Index(
    "idx_conv_last_message_at",
    Conversation.last_message_at.desc()
)

Index(
    "idx_conv_participant_user",
    ConvParticipant.user_id,
    ConvParticipant.conv_id
)

Index(
    "idx_conv_unread_user",
    ConvUnread.user_id
)
