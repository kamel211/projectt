from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageModel(BaseModel):
    sender_id: str
    receiver_id: str
    message: str  # المسار المشفر للملف
    timestamp: datetime
    type: str     # "image" أو "file"
    filename: str
    delivered: bool = False
