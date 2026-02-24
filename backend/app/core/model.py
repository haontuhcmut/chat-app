from sqlmodel import SQLModel, Field, Column, Relationship
import enum
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import DateTime, func, Index, Enum, ForeignKey


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(default=None, unique=True, index=True)
    username: str = Field(default=None, unique=True)
    display_name: str = Field(default=None, nullable=True)
    bio: str = Field(default=None, nullable=True)
    first_name: str = Field(default=None, max_length=32)
    last_name: str = Field(default=None, max_length=32)
    phone: str = Field(default=None, nullable=True)
    avatar_url: str | None = Field(default=None, nullable=True)
    avatar_id: UUID | None = Field(default=None, nullable=True)
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
    conv_id: UUID = Field(default=None, foreign_key="conversation.id", nullable=False)
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
    conversation: "Conversation" = Relationship(
        back_populates="messages",
        sa_relationship_kwargs={"foreign_keys": "[Message.conv_id]"},
    )


class ConvType(str, enum.Enum):
    direct = "direct"
    group = "group"


class Conversation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    type: ConvType = Field(sa_column=Column(Enum(ConvType), nullable=False))

    last_message_id: UUID | None = Field(
        default=None,
        sa_column=Column(
            ForeignKey("message.id", use_alter=True, name="fk_conv_last_message"),
            nullable=True,
        ),
    )

    last_message_at: datetime | None = Field(sa_column=Column(DateTime(timezone=True)))

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
        )
    )

    conv_participants: list["ConvParticipant"] = Relationship(
        back_populates="conversation"
    )
    group_conversation: "GroupConversation" = Relationship(
        back_populates="conversation"
    )

    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"foreign_keys": "[Message.conv_id]"},
    )
    last_message: Message | None = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Conversation.last_message_id]",
            "viewonly": True,
        }
    )


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


class ConvReadState(SQLModel, table=True):
    conv_id: UUID = Field(
        foreign_key="conversation.id",
        primary_key=True,
    )

    user_id: UUID = Field(
        foreign_key="user.id",
        primary_key=True,
    )

    last_message_id: UUID | None = Field(
        foreign_key="message.id",
        nullable=True,
    )

    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
        )
    )


Index("idx_conv_last_message_at", Conversation.last_message_at.desc())

Index("idx_conv_participant_user", ConvParticipant.user_id, ConvParticipant.conv_id)
