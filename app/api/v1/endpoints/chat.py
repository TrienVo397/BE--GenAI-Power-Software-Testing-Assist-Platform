# c:\Users\dorem\Documents\GitHub\BE--GenAI-Power-Software-Testing-Assist-Platform\app\api\v1\endpoints\chat.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from typing import List, Optional, AsyncGenerator, Dict, Any
import uuid
import math
import json
import asyncio
from datetime import datetime
import logging

from app.schemas.chat import (
    ChatSessionCreate, ChatSessionRead, ChatSessionUpdate, ChatSessionWithMessages, ChatSessionCreateSimple,
    ChatMessageRead, ChatListResponse,
    StreamingMessageInput, StreamingChunk, StreamingStatus
)
from app.crud.chat_crud import chat_session_crud, chat_message_crud
from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.config import settings

router = APIRouter()

# Initialize logger
logger = logging.getLogger(__name__)

# Load main system prompt
def load_main_system_prompt() -> str:
    """Load the main system prompt from file"""
    try:
        with open("ai/researchExample/Prompts/main_system_prompt.txt", "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Main system prompt file not found, using default")
        return "You are a helpful QA testing assistant."

# Chat Session Endpoints

@router.post("/sessions", response_model=ChatSessionRead)
def create_chat_session(
    session_simple: ChatSessionCreateSimple,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new chat session.
    Authentication is required via JWT token.
    User ID is automatically set from the authenticated user.
    """
    # Create session data with user ID from current user
    session_data = ChatSessionCreate(
        title=session_simple.title,
        system_prompt=session_simple.system_prompt,
        history_strategy=session_simple.history_strategy,
        memory_type=session_simple.memory_type,
        context_window=session_simple.context_window,
        user_id=current_user.id,
        project_id=session_simple.project_id,
        current_message_sequence_num=session_simple.current_message_sequence_num,
        agent_state=session_simple.agent_state or {},
        graph_id=session_simple.graph_id,
        meta_data=session_simple.meta_data or {},
        memory_config=session_simple.memory_config or {}
    )
    
    # Create the chat session
    chat_session = chat_session_crud.create(
        db=db,
        title=session_data.title,
        user_id=session_data.user_id,
        project_id=session_data.project_id,
        current_message_sequence_num=session_data.current_message_sequence_num,
        agent_state=session_data.agent_state or {},
        graph_id=session_data.graph_id,
        meta_data=session_data.meta_data or {},
        system_prompt=session_data.system_prompt,
        history_strategy=session_data.history_strategy,
        memory_type=session_data.memory_type,
        memory_config=session_data.memory_config or {},
        context_window=session_data.context_window
    )
    
    return chat_session

@router.get("/sessions", response_model=ChatListResponse)
def get_chat_sessions(
    project_id: Optional[uuid.UUID] = Query(None, description="Filter by project ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chat sessions for the current user"""
    skip = (page - 1) * size
    
    if project_id:
        # Get sessions for user and project
        sessions = chat_session_crud.get_by_user_and_project(
            db=db, user_id=current_user.id, project_id=project_id, skip=skip, limit=size
        )
        # Get total count (simplified - in production, add a count method)
        total_sessions = chat_session_crud.get_by_user_and_project(
            db=db, user_id=current_user.id, project_id=project_id, skip=0, limit=1000
        )
        total = len(total_sessions)
    else:
        # Get all sessions for user
        sessions = chat_session_crud.get_by_user(
            db=db, user_id=current_user.id, skip=skip, limit=size
        )
        # Get total count (simplified)
        total_sessions = chat_session_crud.get_by_user(
            db=db, user_id=current_user.id, skip=0, limit=1000
        )
        total = len(total_sessions)
    
    pages = math.ceil(total / size) if total > 0 else 1
    
    return ChatListResponse(
        items=[ChatSessionRead.model_validate(session) for session in sessions],
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/sessions/{session_id}", response_model=ChatSessionRead)
def get_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific chat session"""
    session = chat_session_crud.get(db=db, chat_session_id=session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check if user owns this session
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this chat session"
        )
    
    return session

@router.get("/sessions/{session_id}/messages", response_model=ChatSessionWithMessages)
def get_chat_session_messages(
    session_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200, description="Number of recent messages to include"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a chat session with its messages"""
    session = chat_session_crud.get(db=db, chat_session_id=session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check if user owns this session
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this chat session"
        )
    
    # Get messages
    messages = chat_message_crud.get_latest_messages(db=db, chat_id=session_id, limit=limit)
    
    # Create response with messages
    session_dict = session.dict()
    session_dict["messages"] = messages
    
    return ChatSessionWithMessages(**session_dict)

# Individual Message Operations

@router.put("/sessions/{session_id}/messages/{sequence_num}", response_model=ChatMessageRead)
def update_chat_message(
    session_id: uuid.UUID,
    sequence_num: int,
    content: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a specific chat message"""
    # Verify session exists and user owns it
    session = chat_session_crud.get(db=db, chat_session_id=session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update messages in this chat session"
        )
    
    # Update the message
    updated_message = chat_message_crud.update(
        db=db,
        chat_id=session_id,
        sequence_num=sequence_num,
        content=content
    )
    
    if not updated_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return updated_message

@router.delete("/sessions/{session_id}/messages/{sequence_num}")
def delete_chat_message(
    session_id: uuid.UUID,
    sequence_num: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific chat message"""
    # Verify session exists and user owns it
    session = chat_session_crud.get(db=db, chat_session_id=session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete messages from this chat session"
        )
    
    # Delete the message
    deleted_message = chat_message_crud.delete(
        db=db,
        chat_id=session_id,
        sequence_num=sequence_num
    )
    
    if not deleted_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return {"message": "Chat message deleted successfully"}

@router.put("/sessions/{session_id}", response_model=ChatSessionRead)
def update_chat_session(
    session_id: uuid.UUID,
    session_update: ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a chat session"""
    session = chat_session_crud.get(db=db, chat_session_id=session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check if user owns this session
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this chat session"
        )
    
    # Update the session
    updated_session = chat_session_crud.update(
        db=db,
        chat_session_id=session_id,
        **session_update.dict(exclude_unset=True)
    )
    
    return updated_session

@router.delete("/sessions/{session_id}")
def delete_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session"""
    session = chat_session_crud.get(db=db, chat_session_id=session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check if user owns this session
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this chat session"
        )
    
    # Delete the session
    chat_session_crud.delete(db=db, chat_session_id=session_id)
    
    return {"message": "Chat session deleted successfully"}

# Streaming Endpoints for Real-time LLM Responses

async def stream_llm_response(
    db: Session,
    session_id: uuid.UUID,
    user_message: str,
    user_message_seq: int
) -> AsyncGenerator[str, None]:
    """
    Stream LLM response and save to database
    """
    logger.info(f"Starting LLM response stream for session {session_id}")
    
    # Get session data for context
    session_data = chat_session_crud.get(db=db, chat_session_id=session_id)
    if not session_data:
        yield "data: {\"type\": \"error\", \"error\": \"Session not found\"}\n\n"
        return
    
    # Create streaming AI message
    ai_message = chat_message_crud.create(
        db=db,
        chat_id=session_id,
        content="",  # Will be built incrementally
        message_type="ai",
        parent_id=user_message_seq,
        is_streaming=True,
        stream_complete=False,
        status="streaming",
        meta_data={"generated": True, "parent_sequence": user_message_seq}
    )
    
    # Start streaming
    chunk_sequence = 0
    full_content = ""
    
    try:
        # Send stream start event
        start_chunk = StreamingChunk(
            type="message_start",
            sequence_num=ai_message.sequence_num,
            chunk_sequence=chunk_sequence,
            message_id=f"{session_id}:{ai_message.sequence_num}",
            metadata={"status": "started"}
        )
        yield f"data: {start_chunk.model_dump_json()}\n\n"
        
        # Import and use centralized streaming function
        from ai.agents.conversation_agent import stream_agent_response
        
        # Get previous messages from database and convert to LangChain format
        previous_messages = session_data.get_messages_for_langchain(limit=20)  # Get last 20 messages
        
        # Get configuration
        use_agent = session_data.meta_data.get("use_agent", True) if session_data.meta_data else True
        project_id = session_data.project_id  # Required field - every chat session has a project
        project_context = session_data.meta_data.get("project_context", "") if session_data.meta_data else ""
        
        # Stream content using centralized function
        async for content_delta in stream_agent_response(
            session_id=str(session_id),
            user_message=user_message,
            previous_messages=previous_messages,
            project_id=project_id,
            project_context=project_context,
            additional_data=session_data.agent_state,
            use_tools=use_agent
        ):
            if content_delta:  # Only process non-empty deltas
                chunk_sequence += 1
                full_content += content_delta
                
                # Create content chunk
                content_chunk = StreamingChunk(
                    type="content_chunk",
                    sequence_num=ai_message.sequence_num,
                    chunk_sequence=chunk_sequence,
                    delta=content_delta,
                    content=full_content,
                    message_id=f"{session_id}:{ai_message.sequence_num}"
                )
                chunk_data = f"data: {content_chunk.json()}\n\n"
                logger.info(f"Sending chunk {chunk_sequence}: {content_delta}")
                yield chunk_data
                
                # Add a small delay to ensure chunks are sent individually
                await asyncio.sleep(0.01)
                
                # Update message in database periodically
                if chunk_sequence % 5 == 0:
                    chat_message_crud.update(
                        db=db,
                        chat_id=session_id,
                        sequence_num=ai_message.sequence_num,
                        content=full_content,
                        chunk_sequence=chunk_sequence
                    )
        
        # Finalize message
        final_message = chat_message_crud.update(
            db=db,
            chat_id=session_id,
            sequence_num=ai_message.sequence_num,
            content=full_content,
            is_streaming=False,
            stream_complete=True,
            status="complete",
            chunk_sequence=chunk_sequence
        )
        
        # Send completion event
        end_chunk = StreamingChunk(
            type="message_end",
            sequence_num=ai_message.sequence_num,
            chunk_sequence=chunk_sequence + 1,
            content=full_content,
            message_id=f"{session_id}:{ai_message.sequence_num}",
            metadata={"status": "completed", "total_chunks": chunk_sequence}
        )
        yield f"data: {end_chunk.json()}\n\n"
        
    except Exception as e:
        logger.error(f"Error in LLM response stream: {str(e)}")
        # Handle errors
        error_chunk = StreamingChunk(
            type="error",
            sequence_num=ai_message.sequence_num if 'ai_message' in locals() else None,
            chunk_sequence=chunk_sequence + 1,
            error=str(e),
            message_id=f"{session_id}:{ai_message.sequence_num}" if 'ai_message' in locals() else None
        )
        yield f"data: {error_chunk.json()}\n\n"
        
        # Update message status to error
        if 'ai_message' in locals():
            chat_message_crud.update(
                db=db,
                chat_id=session_id,
                sequence_num=ai_message.sequence_num,
                status="error",
                is_streaming=False,
                stream_complete=True,
                meta_data={"error": str(e)}
            )

@router.post("/sessions/{session_id}/messages/stream")
async def send_streaming_message(
    session_id: uuid.UUID,
    message_input: StreamingMessageInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to a chat session and receive a streaming response"""
    # Verify session exists and user owns it
    session = chat_session_crud.get(db=db, chat_session_id=session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to send messages to this chat session"
        )
    
    # Create the user message
    user_message = chat_message_crud.create(
        db=db,
        chat_id=session_id,
        content=message_input.content,
        message_type=message_input.message_type,
        parent_id=message_input.parent_id,
        meta_data=message_input.meta_data or {}
    )
    
    # Return streaming response
    return StreamingResponse(
        stream_llm_response(db, session_id, message_input.content, user_message.sequence_num),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
