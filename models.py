#models.py

from pydantic import BaseModel, Field
from typing import Optional, List

class Chat(BaseModel):
    id: Optional[int] = None

class User(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class Media(BaseModel):
    file_id: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    is_animated: Optional[bool] = None
    is_video: Optional[bool] = None

class Message(BaseModel):
    chat: Optional[Chat] = None
    from_user: Optional[User] = Field(None, alias="from")
    text: Optional[str] = None
    date: Optional[int] = None
    photo: Optional[List[Media]] = None
    video: Optional[Media] = None
    document: Optional[Media] = None
    audio: Optional[Media] = None
    voice: Optional[Media] = None
    animation: Optional[Media] = None
    sticker: Optional[Media] = None
    video_note: Optional[Media] = None
    caption: Optional[str] = None

class Update(BaseModel):
    update_id: int
    message: Optional[Message] = None
