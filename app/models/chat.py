# c:\Users\dorem\Documents\GitHub\BE--GenAI-Power-Software-Testing-Assist-Platform\app\models\chat.py
from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
from app.models.user import User
from app.models.project import Project


class ChatSession(SQLModel, table=True):
    """Chat session model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str = Field(default="New Chat")
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    user_id: str = Field(foreign_key="user.id")
    project_id: Optional[str] = Field(default=None, foreign_key="project.id")
    
    # LangGraph and Agent State
    agent_state: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Stores the LangGraph agent's state
    graph_id: Optional[str] = Field(default=None)  # ID of the LangGraph instance, if applicable
    meta_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Renamed from 'metadata' to avoid SQLModel conflict
    
    # Relationships
    messages: List["ChatMessage"] = Relationship(back_populates="chat", sa_relationship_kwargs={"cascade": "all, delete"})
    user: User = Relationship(back_populates="chats")
    project: Optional[Project] = Relationship(back_populates="chats")


class ChatMessage(SQLModel, table=True):
    """Individual message in a chat"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Content and metadata
    is_user: bool = Field(default=True)  # True if from user, False if from assistant
    content: str = Field(...)
    node_id: Optional[str] = Field(default=None)  # ID of the LangGraph node that generated this message
    step_id: Optional[str] = Field(default=None)  # ID of the step in the LangGraph execution
    meta_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Additional data like tool calls, reasoning, etc.
    
    # Relationship
    chat_id: str = Field(foreign_key="chat.id")
    chat: ChatSession = Relationship(back_populates="messages")
