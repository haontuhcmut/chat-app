import json
from collections import defaultdict

from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi_pagination.ext.sqlmodel import apaginate
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from .schema import (
    CreateConvRequest,
    ConvType,
    UserConvResponse,
    ConversationResponseItem,
    SeenUserResponse,
    GroupResponse,
    ParticipantResponse,
    ConversationResponse,
    LastMessageSender,
    LastMessageResponse,
)
from uuid import UUID
from sqlmodel import select, func

from ..core.model import (
    Conversation,
    ConvParticipant,
    GroupConversation,
    Message,
    ConvReadState,
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
                        ConvReadState(
                            conv_id=conv.id,
                            user_id=current_me,
                        ),
                        ConvReadState(
                            conv_id=conv.id,
                            user_id=other_user_id,
                        ),
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
                    ConvReadState(conv_id=conv.id, user_id=user_id)
                    for user_id in participants
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
    ) -> ConversationResponse:

        # Load conversations
        stmt = (
            select(Conversation)
            .join(ConvParticipant)
            .where(ConvParticipant.user_id == user_id)
            .options(
                selectinload(Conversation.conv_participants).selectinload(
                    ConvParticipant.user
                ),
                selectinload(Conversation.group_conversation),
            )
            .order_by(Conversation.last_message_at.desc())
        )

        result = await session.exec(stmt)
        convs = result.unique().all()

        if not convs:
            return ConversationResponse(conversations=[])

        conv_ids = [c.id for c in convs]

        # Load read states (1 query)

        read_stmt = select(ConvReadState).where(ConvReadState.conv_id.in_(conv_ids))
        read_result = await session.exec(read_stmt)
        read_states = read_result.all()

        read_map: dict[UUID, dict[UUID, UUID | None]] = defaultdict(dict)
        for r in read_states:
            read_map[r.conv_id][r.user_id] = r.last_message_id

        # Batch load last messages + sender (1 query)

        last_message_ids = [
            c.last_message_id for c in convs if c.last_message_id is not None
        ]

        message_map: dict[UUID, Message] = {}

        if last_message_ids:
            msg_stmt = (
                select(Message)
                .where(Message.id.in_(last_message_ids))
                .options(selectinload(Message.user))
            )
            msg_result = await session.exec(msg_stmt)
            messages = msg_result.all()
            message_map = {m.id: m for m in messages}

        # Build response
        conversation_items: list[ConversationResponseItem] = []

        for conv in convs:

            # ---------- Participants ----------
            if conv.type == ConvType.direct:
                filtered_participants = [
                    p for p in conv.conv_participants if p.user_id != user_id
                ]
            else:
                filtered_participants = conv.conv_participants

            participants = [
                ParticipantResponse(
                    _id=p.user.id,
                    displayName=p.user.display_name,
                    avatarUrl=p.user.avatar_url,
                    joinedAt=p.joined_at,
                )
                for p in filtered_participants
            ]

            # ---------- Group ----------
            group_data = None
            if conv.type == ConvType.group and conv.group_conversation:
                group_data = GroupResponse(
                    name=conv.group_conversation.name,
                    createdBy=conv.group_conversation.created_by,
                )

            # ---------- Seen + Unread ----------
            seen_by: list[SeenUserResponse] = []
            unread_counts: dict[str, int] = {}

            for p in conv.conv_participants:

                user_last_read_id = read_map.get(conv.id, {}).get(p.user_id)

                if not conv.last_message_id:
                    unread_counts[str(p.user_id)] = 0
                    continue

                # Sender always read their own message
                last_message_obj = message_map.get(conv.last_message_id)
                if last_message_obj and last_message_obj.sender_user_id == p.user_id:
                    unread_counts[str(p.user_id)] = 0
                    continue

                # Get last read time
                last_read_time = None

                if user_last_read_id:
                    last_read_msg = message_map.get(user_last_read_id)
                    if last_read_msg:
                        last_read_time = last_read_msg.created_at

                stmt = (
                    select(func.count(Message.id))
                    .where(Message.conv_id == conv.id)
                    .where(Message.sender_user_id != p.user_id)
                )

                if last_read_time:
                    stmt = stmt.where(Message.created_at > last_read_time)

                result = await session.exec(stmt)
                count = result.one()

                unread_counts[str(p.user_id)] = count

                if count == 0:
                    seen_by.append(
                        SeenUserResponse(
                            _id=p.user.id,
                            displayName=p.user.display_name,
                            avatarUrl=p.user.avatar_url,
                        )
                    )

            # ---------- Last Message ----------
            last_message_response = None
            last_message_obj = message_map.get(conv.last_message_id)

            if last_message_obj:
                last_message_response = LastMessageResponse(
                    _id=last_message_obj.id,
                    content=last_message_obj.content or "",
                    createdAt=last_message_obj.created_at,
                    sender=LastMessageSender(
                        _id=last_message_obj.user.id,
                        displayName=last_message_obj.user.display_name,
                        avatarUrl=last_message_obj.user.avatar_url,
                    ),
                )

            # ---------- Build Item ----------
            item = ConversationResponseItem(
                _id=conv.id,
                type=conv.type,
                group=group_data,
                participants=participants,
                lastMessageAt=conv.last_message_at,
                seenBy=seen_by,
                lastMessage=last_message_response,
                unreadCounts=unread_counts,
                createdAt=conv.created_at,
                updatedAt=conv.updated_at,
            )

            conversation_items.append(item)

        return ConversationResponse(conversations=conversation_items)

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
        session: AsyncSession,
    ):
        # ---------- Validate conversation ----------
        conv = await session.get(Conversation, conv_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if not conv.last_message_id:
            return JSONResponse(
                status_code=200,
                content={"message": "No message to mark as read"},
            )

        last_message = await session.get(Message, conv.last_message_id)
        if not last_message:
            return JSONResponse(
                status_code=200,
                content={"message": "Last message not found"},
            )

        if last_message.sender_user_id == user_id:
            return JSONResponse(
                status_code=200,
                content={"message": "Own message - no need to mark as read"},
            )

        stmt = (
            insert(ConvReadState)
            .values(
                conv_id=conv_id,
                user_id=user_id,
                last_message_id=conv.last_message_id,
            )
            .on_conflict_do_update(
                index_elements=["conv_id", "user_id"],
                set_={
                    "last_message_id": conv.last_message_id,
                },
            )
        )

        await session.exec(stmt)
        await session.commit()

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
            "last_message_id": str(conv.last_message_id),
            "seen_by": str(user_id),
        }

        # ---------- Publish Redis ----------
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

    async def get_messages(self, conv_id: UUID, session: AsyncSession):
        stmt = select(Message).where(Message.conv_id == conv_id)
        return await apaginate(session, stmt)
