import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .schema import CreateDirectMessage, CreateGroupMessage
from ..conversations.schema import ConvType
from ..core.model import Conversation, ConvParticipant, Message, ConvReadState
from ..core.redis import redis_client
from ..friends.services import FriendshipService


class MessageService:
    async def send_direct_message(
        self,
        data: CreateDirectMessage,
        current_me: UUID,
        friendship: FriendshipService,
        session: AsyncSession,
    ) -> Message:

        # Validate
        if not data.content and not data.img_url:
            raise HTTPException(
                status_code=400,
                detail="Message must have content or image",
            )

        # Check friendship
        await friendship.assert_direct_friend(
            user_id=current_me,
            target_id=data.recipient_id,
            session=session,
        )

        # Find existing direct conversation
        stmt = (
            select(Conversation)
            .join(ConvParticipant)
            .where(
                Conversation.type == ConvType.direct,
                ConvParticipant.user_id.in_([current_me, data.recipient_id]),
            )
            .group_by(Conversation.id)
            .having(func.count(ConvParticipant.user_id) == 2)
            .limit(1)
        )

        conv = await session.scalar(stmt)

        # Create conversation if not exists
        if not conv:
            conv = Conversation(type=ConvType.direct)
            session.add(conv)
            await session.flush()

            session.add_all(
                [
                    ConvParticipant(conv_id=conv.id, user_id=current_me),
                    ConvParticipant(conv_id=conv.id, user_id=data.recipient_id),
                    ConvReadState(conv_id=conv.id, user_id=current_me),
                    ConvReadState(conv_id=conv.id, user_id=data.recipient_id),
                ]
            )

            await session.flush()

        # Always create message
        message = Message(
            conv_id=conv.id,
            sender_user_id=current_me,
            content=data.content,
            img_url=data.img_url,
        )

        session.add(message)
        await session.flush()

        # Update conversation metadata
        conv.last_message_at = message.created_at
        conv.last_message_id = message.id

        # Update sender read state (O(1) system)
        stmt = select(ConvReadState).where(
            ConvReadState.conv_id == conv.id,
            ConvReadState.user_id == current_me,
        )
        read_state = await session.scalar(stmt)

        if read_state:
            read_state.last_message_id = message.id

        await session.commit()

        # Publish Redis event
        await redis_client.publish(
            "broadcast",
            json.dumps(
                {
                    "key": f"user:{data.recipient_id}",
                    "data": {
                        "event": "new_message",
                        "message_id": str(message.id),
                        "conv_id": str(conv.id),
                        "sender_id": str(current_me),
                        "content": message.content,
                        "img_url": message.img_url,
                        "created_at": message.created_at.isoformat(),
                    },
                }
            ),
        )

        return message

    async def send_group_message(
        self,
        data: CreateGroupMessage,
        current_me: UUID,
        session: AsyncSession,
    ) -> Message:

        # ---------- Validate ----------
        if not data.content and not data.img_url:
            raise HTTPException(
                status_code=400,
                detail="Message must have content or image",
            )

        # ---------- Get conversation ----------
        conv = await session.get(Conversation, data.conv_id)

        if not conv or conv.type != ConvType.group:
            raise HTTPException(status_code=404, detail="Group not found")

        # ---------- Check membership ----------
        stmt = select(ConvParticipant).where(
            ConvParticipant.conv_id == conv.id,
            ConvParticipant.user_id == current_me,
        )
        participant = await session.scalar(stmt)

        if not participant:
            raise HTTPException(status_code=403, detail="Not a group member")

        # ---------- Create message ----------
        message = Message(
            conv_id=conv.id,
            sender_user_id=current_me,
            content=data.content,
            img_url=data.img_url,
        )

        session.add(message)
        await session.flush()

        # ---------- Update conversation metadata ----------
        conv.last_message_id = message.id
        conv.last_message_at = message.created_at

        # ---------- Update sender read state ----------
        stmt = select(ConvReadState).where(
            ConvReadState.conv_id == conv.id,
            ConvReadState.user_id == current_me,
        )

        read_state = await session.scalar(stmt)

        if read_state:
            read_state.last_message_id = message.id

        await session.commit()

        # ---------- Get other members ----------
        stmt = select(ConvParticipant.user_id).where(
            ConvParticipant.conv_id == conv.id,
            ConvParticipant.user_id != current_me,
        )

        result = await session.exec(stmt)
        receivers = result.all()

        # ---------- Publish Redis ----------
        payload = {
            "event": "new_message",
            "message_id": str(message.id),
            "conv_id": str(conv.id),
            "sender_id": str(current_me),
            "content": message.content,
            "img_url": message.img_url,
            "created_at": message.created_at.isoformat(),
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

        return message
