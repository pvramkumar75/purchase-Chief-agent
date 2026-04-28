from typing import Optional
from pydantic import BaseModel, Field

class ChatCreateRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)


class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    use_knowledge: bool = True


class ChatResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class MessageResponse(BaseModel):
    id: int
    chat_id: str
    role: str
    content: str
    created_at: str


class AttachmentResponse(BaseModel):
    id: str
    chat_id: str
    original_name: str
    stored_path: str
    mime_type: Optional[str]
    char_count: int
    created_at: str


class ChatMessageReply(BaseModel):
    chat_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse
    knowledge_hits: int
