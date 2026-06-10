from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChatMessage(BaseModel):
    id: Optional[str] = None
    sender_id: str
    sender_name: str
    sender_role: str
    recipient_id: str
    message_type: str = "text"
    content: str
    timestamp: Optional[datetime] = None
    read: bool = False
    delivered: bool = False
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    is_offline: bool = False