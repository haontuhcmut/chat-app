from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

class CreateMessage(BaseModel):
    content: str
    img_url: str | None = None
    recipient_id: UUID

class UpdateConvFromNewMess(BaseModel):
    last_message_content: str
    last_message_sender_id: UUID
    last_message_at: datetime | None = datetime.now()

