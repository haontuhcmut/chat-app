import json
from datetime import datetime

from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.dialects.postgresql.dml import insert
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from .schema import (
    CreateConvRequest,
    ConvType,
    ConversationResponse,
    ParticipantResponse,
    UserConvResponse,
)
from uuid import UUID
from sqlmodel import select, func

from ..core.model import (
    Conversation,
    ConvParticipant,
    GroupConversation,
    ConvUnread,
    ConvSeen,
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

                session.add_all(
                    [
                        ConvParticipant(conv_id=conv.id, user_id=uid)
                        for uid in participants
                    ]
                )

                return conv

    async def get_all_convs(
        self,
        current_me: UUID,
        session: AsyncSession,
    ):
        stmt = (
            select(Conversation)
            .join(ConvParticipant)
            .where(ConvParticipant.user_id == current_me)
            .options(
                selectinload(Conversation.conv_participants).selectinload(
                    ConvParticipant.user
                )
            )
            .order_by(Conversation.last_message_at.desc())
        )

        result = await session.exec(stmt)
        conversations = result.all()

        conv_ids = [conv.id for conv in conversations]

        unread_stmt = select(ConvUnread.conv_id, ConvUnread.unread_count).where(
            ConvUnread.user_id == current_me,
            ConvUnread.conv_id.in_(conv_ids),
        )

        unread_result = await session.exec(unread_stmt)
        unread_map = {
            conv_id: unread_count for conv_id, unread_count in unread_result.all()
        }

        items = [
            ConversationResponse(
                id=conv.id,
                type=conv.type,
                last_message_content=conv.last_message_content,
                last_message_at=conv.last_message_at,
                unread_count=unread_map.get(conv.id, 0),
                participants=[
                    ParticipantResponse(
                        user_id=p.user.id,
                        username=p.user.username,
                        avatar_url=p.user.avatar_url,
                        joined_at=p.joined_at,
                    )
                    for p in conv.conv_participants
                    if p.user and p.user_id != current_me
                ],
            )
            for conv in conversations
        ]

        return items

    async def get_user_conversations_for_websocket(
        self, user_id: UUID, session: AsyncSession
    ):
        stmt = select(ConvParticipant).where(ConvParticipant.user_id == user_id)
        result = await session.exec(stmt)
        conv = result.all()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return [UserConvResponse.model_validate(c) for c in conv]

    async def mark_as_seen(self, conv_id: UUID, user_id: UUID, session: AsyncSession):
        conv = await session.get(Conversation, conv_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if not conv.last_message_content:
            raise HTTPException(
                status_code=404, detail="Could not find message to mark as seen"
            )

        if conv.last_message_sender_id == user_id:
            return JSONResponse(status_code=200, content={"message": "Nothing to update"})


        unread = await session.get(ConvUnread, (user_id, conv_id))
        if unread:
            unread.unread_count = 0

        # Upsert technique replace the get->update->add
        stmt = insert(ConvSeen).values(
            conv_id=conv_id,
            user_id=user_id,
        ).on_conflict_do_update(
            index_elements=["conv_id", "user_id"], # detected conflict
            set_={"seen_at": func.now()}, # update record
        )

        await session.exec(stmt)
        await session.commit()

        seen_conv = await session.get(ConvSeen, (conv_id, user_id))

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
            "last_message_content": conv.last_message_content,
            "last_message_at": conv.last_message_at,
            "seen_by": str(user_id),
            "seen_at": seen_conv.seen_at,
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
                "message": "Marked as seen",
                "seen_by": str(user_id),
                "my_unread_count": 0,
            },
        )
