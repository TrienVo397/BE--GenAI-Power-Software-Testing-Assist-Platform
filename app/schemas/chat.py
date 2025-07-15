# c:\Users\dorem\Documents\GitHub\BE--GenAI-Power-Software-Testing-Assist-Platform\app\schemas\chat.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# ChatSession Schemas
class ChatSessionBase(BaseModel):
    title: str = "New Chat"
    system_prompt: Optional[str] = None
    history_strategy: str = "all"
    memory_type: str = "default"
    context_window: int = 10

class ChatSessionCreate(ChatSessionBase):
    user_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    current_message_sequence_num: int = 0
    agent_state: Optional[Dict[str, Any]] = None
    graph_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    memory_config: Optional[Dict[str, Any]] = None

class ChatSessionCreateSimple(ChatSessionBase):
    project_id: Optional[uuid.UUID] = None
    current_message_sequence_num: int = 0
    agent_state: Optional[Dict[str, Any]] = None
    graph_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    memory_config: Optional[Dict[str, Any]] = None

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    system_prompt: Optional[str] = None
    history_strategy: Optional[str] = None
    memory_type: Optional[str] = None
    context_window: Optional[int] = None
    current_message_sequence_num: Optional[int] = None
    agent_state: Optional[Dict[str, Any]] = None
    graph_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    memory_config: Optional[Dict[str, Any]] = None

class ChatSessionRead(ChatSessionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    current_message_sequence_num: int
    agent_state: Dict[str, Any]
    graph_id: Optional[str] = None
    meta_data: Dict[str, Any]
    memory_config: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)

class ChatSessionWithMessages(ChatSessionRead):
    messages: List["ChatMessageRead"] = []

# ChatMessage Schemas
class ChatMessageBase(BaseModel):
    content: str
    message_type: str = "human"
    status: str = "complete"

class ChatMessageCreate(ChatMessageBase):
    chat_id: uuid.UUID
    parent_id: Optional[int] = None
    additional_kwargs: Optional[Dict[str, Any]] = None
    function_name: Optional[str] = None
    function_args: Optional[Dict[str, Any]] = None
    function_output: Optional[Dict[str, Any]] = None
    node_id: Optional[str] = None
    step_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    is_streaming: bool = False
    stream_complete: bool = True
    chunk_sequence: int = 0
    status_details: Optional[str] = None
    importance_score: Optional[float] = None
    embedding_id: Optional[str] = None

class ChatMessageUpdate(BaseModel):
    content: Optional[str] = None
    message_type: Optional[str] = None
    status: Optional[str] = None
    additional_kwargs: Optional[Dict[str, Any]] = None
    function_name: Optional[str] = None
    function_args: Optional[Dict[str, Any]] = None
    function_output: Optional[Dict[str, Any]] = None
    node_id: Optional[str] = None
    step_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    is_streaming: Optional[bool] = None
    stream_complete: Optional[bool] = None
    chunk_sequence: Optional[int] = None
    status_details: Optional[str] = None
    importance_score: Optional[float] = None
    embedding_id: Optional[str] = None

class ChatMessageRead(ChatMessageBase):
    sequence_num: int
    chat_id: uuid.UUID
    parent_id: Optional[int] = None
    created_at: datetime
    additional_kwargs: Dict[str, Any]
    function_name: Optional[str] = None
    function_args: Optional[Dict[str, Any]] = None
    function_output: Optional[Dict[str, Any]] = None
    node_id: Optional[str] = None
    step_id: Optional[str] = None
    meta_data: Dict[str, Any]
    is_streaming: bool
    stream_complete: bool
    chunk_sequence: int
    status_details: Optional[str] = None
    importance_score: Optional[float] = None
    embedding_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Request/Response Schemas
class ChatMessageInput(BaseModel):
    """Schema for sending a message to a chat"""
    content: str
    message_type: str = "human"
    parent_id: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = None

class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    user_message: ChatMessageRead
    ai_message: Optional[ChatMessageRead] = None

class ChatListResponse(BaseModel):
    """Schema for chat list response"""
    items: List[ChatSessionRead]
    total: int
    page: int
    size: int
    pages: int

class ChatMessagesResponse(BaseModel):
    """Schema for chat messages response"""
    items: List[ChatMessageRead]
    total: int
    page: int
    size: int
    pages: int

class ChatStatusUpdate(BaseModel):
    """Schema for updating chat message status"""
    status: str
    status_details: Optional[str] = None

class StreamingUpdate(BaseModel):
    """Schema for streaming message updates"""
    is_streaming: bool
    stream_complete: bool = True
    chunk_sequence: Optional[int] = None
    content: Optional[str] = None

class StreamingMessageInput(BaseModel):
    """Schema for sending a message that expects a streaming response"""
    content: str
    message_type: str = "human"
    parent_id: Optional[int] = None # Remember to pass the parent message sequence number for threading
    meta_data: Optional[Dict[str, Any]] = None
    stream: bool = True

class StreamingChunk(BaseModel):
    """Schema for individual streaming chunks"""
    type: str  # "message_start", "content_chunk", "message_end", "error"
    sequence_num: Optional[int] = None
    chunk_sequence: int
    content: Optional[str] = None
    delta: Optional[str] = None  # Content delta for this chunk
    message_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class StreamingStatus(BaseModel):
    """Schema for streaming status updates"""
    session_id: uuid.UUID
    message_sequence_num: int
    status: str  # "started", "streaming", "completed", "error"
    timestamp: datetime
    chunk_count: int = 0
    total_content_length: int = 0
