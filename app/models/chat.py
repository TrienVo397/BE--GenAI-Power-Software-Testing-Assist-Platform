# c:\Users\dorem\Documents\GitHub\BE--GenAI-Power-Software-Testing-Assist-Platform\app\models\chat.py
import logging
from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import uuid
from datetime import datetime, timezone
from langchain_core.messages import (
    AnyMessage, HumanMessage, AIMessage, 
    SystemMessage, ToolMessage, FunctionMessage
)

if TYPE_CHECKING:
    from .user import User
    from .project import Project


class ChatSession(SQLModel, table=True):
    """Chat session model"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(default="New Chat", nullable=False)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    
    current_message_sequence_num: int = Field(default=0, nullable=False, index=True)  # Tracks the sequence number of the last message
    
    # Foreign keys
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True, nullable=False)
    project_id: uuid.UUID = Field(foreign_key="project.id", index=True, nullable=False)  # Every chat session must belong to a project
    
    # LangChain/LangGraph State Management
    agent_state: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Stores the LangGraph agent's state
    graph_id: Optional[str] = Field(default=None, nullable=True)  # ID of the LangGraph instance, if applicable
    meta_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Renamed from 'metadata' to avoid SQLModel conflict
    system_prompt: Optional[str] = Field(default=None, nullable=True)  # System prompt for this session
    history_strategy: str = Field(default="all", nullable=False)  # Options: all, window, summarized (for future use)
    
    # Memory persistence configuration
    memory_type: str = Field(default="default", nullable=False)  # Type of memory strategy (vector, buffer, hybrid) (for future use)
    memory_config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Configuration for memory (for future use)
    context_window: int = Field(default=10, nullable=False)  # Number of messages to include in context window
    
    # Relationships
    messages: List["ChatMessage"] = Relationship(back_populates="chat", sa_relationship_kwargs={"cascade": "all, delete"})
    user: "User" = Relationship(back_populates="chats")
    project: "Project" = Relationship(back_populates="chats")  # Required relationship to project
    
    # Add logging for critical operations
    def __init__(self, **data):
        super().__init__(**data)
        logging.info(f"Chat session created: {self.id}")
    
    def get_messages_for_langchain(self, limit: Optional[int] = None) -> List[AnyMessage]:
        """
        Convert chat messages to LangChain format for passing to LLM.
        
        Args:
            limit: Optional number of most recent messages to include
            
        Returns:
            List of LangChain message objects ready to use with LLMs
        """
        # Start with system message if available
        messages = []
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
        
        # Get chat messages from database
        query_messages = sorted(self.messages, key=lambda x: x.created_at)
        
        # Apply limit if specified based on history strategy
        if self.history_strategy == "window" and limit:
            query_messages = query_messages[-limit:]
        
        # Convert each message to LangChain format
        for msg in query_messages:
            if not msg.is_streaming or msg.stream_complete:  # Skip incomplete messages
                messages.append(to_langchain_message(msg))
        
        return messages
        
    def add_langchain_message(self, message: AnyMessage) -> "ChatMessage":
        """
        Add a LangChain message to this chat session.
        
        Args:
            message: A LangChain message object
            
        Returns:
            The created ChatMessage database object
        """
        # Convert LangChain message to our ChatMessage model
        chat_message = from_langchain_message(message, str(self.id))
        
        # Note: The actual persistence needs to be handled by the repository/crud layer
        return chat_message


class ChatMessage(SQLModel, table=True):
    """Individual message in a chat"""
    # Manage the message in the chat (0->...) instead of id to avoid id exhaustion and saved memory
    # Using composite primary key with chat_id and sequence_num
    sequence_num: int = Field(default=0, nullable=False, index=True, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Content and metadata
    parent_id: Optional[int] = Field(default=None, nullable=True, index=True)  # For threaded messages - references sequence_num
    content: str = Field(nullable=False)
    
    # LangChain/LangGraph Message Type Support
    message_type: str = Field(default="human", nullable=False)  # Options: human, ai, system, function, tool
    additional_kwargs: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Additional message-specific parameters
    
    # For Function/Tool Messages
    function_name: Optional[str] = Field(default=None, nullable=True)  # For function/tool messages
    function_args: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # Function arguments
    function_output: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # Function return value
    
    # LangGraph tracking
    node_id: Optional[str] = Field(default=None, nullable=True)  # ID of the LangGraph node that generated this message
    step_id: Optional[str] = Field(default=None, nullable=True)  # ID of the step in the LangGraph execution
    meta_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Additional data like tool calls, reasoning, etc.
    
    # Stream-specific fields
    is_streaming: bool = Field(default=False, nullable=False)  # Whether this message is currently streaming
    stream_complete: bool = Field(default=True, nullable=False)  # Whether streaming is complete for this message
    chunk_sequence: int = Field(default=0, nullable=False)  # Ordering for stream chunks
    
    # Message status
    status: str = Field(default="complete", nullable=False)  # Status: pending, streaming, complete, error
    status_details: Optional[str] = Field(default=None, nullable=True)  # Additional details about status
    
    # Memory and retrieval fields
    importance_score: Optional[float] = Field(default=None, nullable=True)  # Score for memory persistence (for future use)
    embedding_id: Optional[str] = Field(default=None, nullable=True)  # ID of vector embedding if stored (for future use)
    
    # Foreign key
    chat_id: uuid.UUID = Field(foreign_key="chatsession.id", index=True, nullable=False, primary_key=True)
    
    # Relationships
    chat: "ChatSession" = Relationship(back_populates="messages")
    
    # Add logging for critical operations
    def __init__(self, **data):
        super().__init__(**data)
        logging.info(f"Chat message created: {self.sequence_num} in chat {self.chat_id}")


# Helper methods for LangChain message conversion
def to_langchain_message(message: ChatMessage) -> AnyMessage:
    """Convert a ChatMessage to a LangChain message class instance."""
    # Common kwargs for all message types
    additional_kwargs = message.additional_kwargs or {}
    
    if message.message_type == "human":
        return HumanMessage(content=message.content, additional_kwargs=additional_kwargs)
    elif message.message_type == "ai":
        return AIMessage(content=message.content, additional_kwargs=additional_kwargs)
    elif message.message_type == "system":
        return SystemMessage(content=message.content, additional_kwargs=additional_kwargs)
    elif message.message_type == "tool":
        tool_call_id = message.function_name or str(uuid.uuid4())
        return ToolMessage(
            content=message.content,
            tool_call_id=tool_call_id,
            additional_kwargs=additional_kwargs
        )
    elif message.message_type == "function":
        # Ensure function name is not None
        name = message.function_name or "unknown_function"
        return FunctionMessage(
            content=message.content,
            name=name,
            additional_kwargs=additional_kwargs
        )
    else:
        # Default fallback
        return HumanMessage(content=message.content, additional_kwargs=additional_kwargs)

def from_langchain_message(message: AnyMessage, chat_id: str) -> ChatMessage:
    """Create a ChatMessage from a LangChain message class instance."""
    # Base message data
    message_data = {
        "chat_id": uuid.UUID(chat_id),
        "content": message.content,
        "additional_kwargs": message.additional_kwargs or {}
    }
    
    # Set message type and specific fields based on message class
    if isinstance(message, HumanMessage):
        message_data["message_type"] = "human"
    elif isinstance(message, AIMessage):
        message_data["message_type"] = "ai"
    elif isinstance(message, SystemMessage):
        message_data["message_type"] = "system"
    elif isinstance(message, ToolMessage):
        message_data["message_type"] = "tool"
        message_data["function_name"] = getattr(message, 'name', None) or getattr(message, 'tool_call_id', None)
    elif isinstance(message, FunctionMessage):
        message_data["message_type"] = "function"
        message_data["function_name"] = message.name
        # Extract function args and outputs if available
        if "args" in message.additional_kwargs:
            message_data["function_args"] = message.additional_kwargs.get("args")
        if "result" in message.additional_kwargs:
            message_data["function_output"] = message.additional_kwargs.get("result")
    
    return ChatMessage(**message_data)
