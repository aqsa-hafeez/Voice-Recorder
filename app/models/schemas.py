from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SegmentOut(BaseModel):
    speaker_label: str
    text: str
    start_time: float
    end_time: float

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    title: str
    language_detected: Optional[str]
    duration_sec: Optional[float]
    status: str
    created_at: datetime
    has_audio: bool = False

    class Config:
        from_attributes = True


class ConversationDetailOut(ConversationOut):
    segments: List[SegmentOut] = []


class ConversationUpdate(BaseModel):
    title: str
