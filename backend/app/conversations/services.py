import json

from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from .schema import (
    CreateConvRequest,
    ConvType,
    UserConvResponse,
)
from uuid import UUID
from sqlmodel import select, func, desc

from ..core.model import (
    Conversation,
    ConvParticipant,
    GroupConversation,
    Message, ConvReadState,
)
from ..core.redis import redis_client
from ..friends.services import FriendshipService


class ConvServices:
    async def create_conv(
        self,
        current_me: UUID,
        data: CreateConvRequest,
        friendship: FriendshipService,
        session: AsyncSession,
    ):
        if data.type == ConvType.group and not data.name:
            raise HTTPException(status_code=400, detail="Group name is required")

        async with session.begin():
            if data.type == ConvType.direct:
                if len(data.member_id) != 1:
                    raise HTTPException(
                        400, "Direct conversation must have exactly 1 member"
                    )
                await friendship.assert_direct_friend(
                    current_me, data.member_id[0], session
                )

                other_user_id = data.member_id[0]

                # find existing direct conversation with BOTH users
                subq = (
                    select(ConvParticipant.conv_id)
                    .where(ConvParticipant.user_id.in_([current_me, other_user_id]))
                    .group_by(ConvParticipant.conv_id)
                    .having(func.count(ConvParticipant.user_id) == 2)
                    .subquery()
                )

                # Use a subquery to query that these two members belong to the direct type
                stmt = select(Conversation).where(
                    Conversation.type == ConvType.direct,
                    Conversation.id.in_(select(subq.c.conv_id)),
                )

                result = await session.exec(stmt)
                conv = result.first()

                if conv:
                    return conv

                # create new direct conversation
                conv = Conversation(type=ConvType.direct)
                session.add(conv)
                await session.flush()

                session.add_all(
                    [
                        ConvReadState(conv_id=conv.id, user_id=current_me, last_message_content=None),
                        ConvReadState(conv_id=conv.id, user_id=other_user_id, last_message_content=None),
                    ]
                )

                session.add_all(
                    [
                        ConvParticipant(conv_id=conv.id, user_id=current_me),
                        ConvParticipant(conv_id=conv.id, user_id=other_user_id),
                    ]
                )

                return conv

            if data.type == ConvType.group:
                await friendship.assert_group_friends(
                    current_me, data.member_id, session
                )

                conv = Conversation(type=ConvType.group)
                session.add(conv)
                await session.flush()

                session.add(
                    GroupConversation(
                        conv_id=conv.id,
                        name=data.name,
                        created_by=current_me,
                    )
                )

                participants = set(data.member_id)
                participants.add(current_me)

                read_states = [
                    ConvReadState(conv_id=conv.id, user_id=user_id, last_message_content=None) for user_id in participants
                ]
                session.add_all(read_states)

                session.add_all(
                    [
                        ConvParticipant(conv_id=conv.id, user_id=uid)
                        for uid in participants
                    ]
                )

                return conv

    async def get_all_convs(
        self,
        user_id: UUID,
        session: AsyncSession,
    ):
        conv_stmt = (
            select(Conversation)
            .join(ConvParticipant, ConvParticipant.conv_id == Conversation.id)
            .where(ConvParticipant.user_id == user_id)
            .options(
                selectinload(Conversation.messages),
                selectinload(Conversation.conv_participants)
        ))

        result = await session.exec(conv_stmt)
        convs = result.unique().all()
        return convs

    async def get_user_conversations_for_websocket(
        self, user_id: UUID, session: AsyncSession
    ):
        stmt = select(ConvParticipant).where(ConvParticipant.user_id == user_id)
        result = await session.exec(stmt)
        conv = result.all()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return [UserConvResponse.model_validate(c) for c in conv]

    async def mark_as_seen(
            self,
            conv_id: UUID,
            user_id: UUID,
            session: AsyncSession
    ):
        # validate
        conv = await session.get(Conversation, conv_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if not conv.last_message_at:
            return JSONResponse(
                status_code=200,
                content={"message": "No message to mark as read"}
            )

        # getting last message
        stmt = (
            select(Message.id)
            .where(Message.conv_id == conv_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )

        result = await session.exec(stmt)
        latest_message_id = result.first()

        if not latest_message_id:
            return JSONResponse(
                status_code=200,
                content={"message": "No message found"}
            )

        # Upsert ConvReadState
        stmt = (
            insert(ConvReadState)
            .values(
                conv_id=conv_id,
                user_id=user_id,
                last_message_id=latest_message_id,
                last_read_at=func.now(),
            )
            .on_conflict_do_update(
                index_elements=["conv_id", "user_id"],
                set_={
                    "last_message_id": latest_message_id,
                    "last_read_at": func.now(),
                },
            )
        )

        await session.exec(stmt)
        await session.commit()

        # getting participant other
        stmt = (
            select(ConvParticipant.user_id)
            .where(ConvParticipant.conv_id == conv_id)
            .where(ConvParticipant.user_id != user_id)
        )

        result = await session.exec(stmt)
        receivers = result.all()

        payload = {
            "event": "read-message",
            "conv_id": str(conv_id),
            "last_message_id": str(latest_message_id),
            "seen_by": str(user_id),
        }

        for uid in receivers:
            await redis_client.publish(
                "broadcast",
                json.dumps(
                    {
                        "key": f"user:{uid}",
                        "data": payload,
                    }
                ),
            )

        return JSONResponse(
            status_code=200,
            content={
                "message": "Marked as read",
                "seen_by": str(user_id),
            },
        )
