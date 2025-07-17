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
    ChatMessageCreate, ChatMessageRead, ChatMessageUpdate, ChatMessageInput,
    ChatMessageResponse, ChatListResponse, ChatMessagesResponse,
    ChatStatusUpdate, StreamingUpdate, StreamingMessageInput, StreamingChunk, StreamingStatus
)
from app.crud.chat_crud import chat_session_crud, chat_message_crud
from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.config import settings
import logging

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

@router.get("/sessions/{session_id}/with-messages", response_model=ChatSessionWithMessages)
def get_chat_session_with_messages(
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

# Chat Message Endpoints

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
def send_message(
    session_id: uuid.UUID,
    message_input: ChatMessageInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to a chat session"""
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
    
    # Generate AI response using centralized LLM functions
    ai_message = None
    if message_input.message_type == "human":
        try:
            # Import here to avoid circular imports
            from ai.agents.conversation_agent import get_agent_response
            
            # Get session data for context
            session_data = chat_session_crud.get(db=db, chat_session_id=session_id)
            if not session_data:
                raise Exception("Session not found")
                
            # Get response using centralized function
            use_agent = session_data.meta_data.get("use_agent", True) if session_data.meta_data else True
            project_name = session_data.meta_data.get("project_name", "Default Project") if session_data.meta_data else "Default Project"
            
            ai_response, updated_agent_state = get_agent_response(
                session_id=str(session_id),
                user_message=message_input.content,
                user_message_seq=user_message.sequence_num,
                session_agent_state=session_data.agent_state,
                project_name=project_name,
                use_tools=use_agent
            )
            
            # Update session with new agent state
            chat_session_crud.update(
                db=db,
                chat_session_id=session_id,
                agent_state=updated_agent_state
            )
            
            # Create AI message
            ai_message = chat_message_crud.create(
                db=db,
                chat_id=session_id,
                content=ai_response,
                message_type="ai",
                parent_id=user_message.sequence_num,
                meta_data={"generated": True, "method": "centralized_agent"}
            )
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            # Create fallback response
            ai_message = chat_message_crud.create(
                db=db,
                chat_id=session_id,
                content=f"I apologize, but I encountered an error while processing your request: {str(e)}",
                message_type="ai",
                parent_id=user_message.sequence_num,
                meta_data={"generated": True, "error": str(e)}
            )
    
    return ChatMessageResponse(
        user_message=ChatMessageRead.model_validate(user_message),
        ai_message=ChatMessageRead.model_validate(ai_message) if ai_message else None
    )

@router.get("/sessions/{session_id}/messages", response_model=ChatMessagesResponse)
def get_chat_messages(
    session_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=200, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get messages from a chat session"""
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
            detail="Not authorized to access messages from this chat session"
        )
    
    # Get messages with pagination
    skip = (page - 1) * size
    messages = chat_message_crud.get_by_chat(db=db, chat_id=session_id, skip=skip, limit=size)
    
    # Get total count (simplified)
    all_messages = chat_message_crud.get_by_chat(db=db, chat_id=session_id, skip=0, limit=1000)
    total = len(all_messages)
    
    pages = math.ceil(total / size) if total > 0 else 1
    
    return ChatMessagesResponse(
        items=[ChatMessageRead.model_validate(message) for message in messages],
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/sessions/{session_id}/messages/{sequence_num}", response_model=ChatMessageRead)
def get_chat_message(
    session_id: uuid.UUID,
    sequence_num: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific message from a chat session"""
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
            detail="Not authorized to access this chat session"
        )
    
    # Get the message
    message = chat_message_crud.get(db=db, chat_id=session_id, sequence_num=sequence_num)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return message

@router.put("/sessions/{session_id}/messages/{sequence_num}", response_model=ChatMessageRead)
def update_chat_message(
    session_id: uuid.UUID,
    sequence_num: int,
    message_update: ChatMessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a chat message"""
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
        **message_update.dict(exclude_unset=True)
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
    """Delete a chat message"""
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
    deleted_message = chat_message_crud.delete(db=db, chat_id=session_id, sequence_num=sequence_num)
    if not deleted_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return {"message": "Message deleted successfully"}

# Streaming and Status Endpoints

@router.patch("/sessions/{session_id}/messages/{sequence_num}/status", response_model=ChatMessageRead)
def update_message_status(
    session_id: uuid.UUID,
    sequence_num: int,
    status_update: ChatStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the status of a chat message"""
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
            detail="Not authorized to update message status in this chat session"
        )
    
    # Update the message status
    updated_message = chat_message_crud.update_status(
        db=db,
        chat_id=session_id,
        sequence_num=sequence_num,
        status=status_update.status,
        status_details=status_update.status_details
    )
    
    if not updated_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return updated_message

@router.patch("/sessions/{session_id}/messages/{sequence_num}/streaming", response_model=ChatMessageRead)
def update_streaming_status(
    session_id: uuid.UUID,
    sequence_num: int,
    streaming_update: StreamingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the streaming status of a chat message"""
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
            detail="Not authorized to update streaming status in this chat session"
        )
    
    # Update the streaming status
    update_data = streaming_update.dict(exclude_unset=True)
    updated_message = chat_message_crud.update(
        db=db,
        chat_id=session_id,
        sequence_num=sequence_num,
        **update_data
    )
    
    if not updated_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return updated_message

@router.get("/sessions/{session_id}/messages/streaming", response_model=List[ChatMessageRead])
def get_streaming_messages(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all streaming messages from a chat session"""
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
            detail="Not authorized to access this chat session"
        )
    
    # Get streaming messages
    streaming_messages = chat_message_crud.get_streaming_messages(db=db, chat_id=session_id)
    
    return streaming_messages


# Streaming Endpoints for Real-time LLM Responses

async def simulate_llm_response(user_message: str, session_id: uuid.UUID, message_sequence_num: int) -> AsyncGenerator[str, None]:
    """
    Simulate an LLM response stream. 
    Replace this with your actual LLM integration (OpenAI, Anthropic, etc.)
    """
    # Simulate AI processing the message
    response_parts = [
        "I understand your question about ",
        f'"{user_message}". ',
        "Let me think about this... ",
        "Based on my knowledge, ",
        "I would say that this is an interesting topic. ",
        "Here's my detailed response: ",
        "This involves several considerations that ",
        "we should explore together. ",
        "Would you like me to elaborate on any specific aspect?"
    ]
    
    for i, part in enumerate(response_parts):
        await asyncio.sleep(0.2)  # Simulate processing delay
        yield part

async def stream_agent_response(
    db: Session,
    session_id: uuid.UUID,
    user_message: str,
    user_message_seq: int,
    session_data: ChatSession
) -> AsyncGenerator[str, None]:
    """
    Stream real LLM response using the conversation agent
    """
    logger.info(f"Starting agent response stream for session {session_id}")
    
    try:
        # Import here to avoid circular imports
        from ai.agents.conversation_agent import graph, AgentState, llm
        
        # Load or create agent state from session
        agent_state = session_data.agent_state or {}
        
        # Initialize conversation state if not exists
        if not agent_state.get("initialized"):
            main_system_prompt = load_main_system_prompt()
            conversation_state = AgentState(
                messages=[SystemMessage(content=main_system_prompt)],
                project_name=session_data.meta_data.get("project_name", "Default Project"),
                context=agent_state.get("context", ""),
                requirements=agent_state.get("requirements", []),
                testCases=agent_state.get("testCases", [])
            )
            agent_state["initialized"] = True
        else:
            # Restore conversation state from session
            conversation_state = AgentState(
                messages=[
                    SystemMessage(content=load_main_system_prompt()),
                    # Add previous messages if needed
                ],
                project_name=session_data.meta_data.get("project_name", "Default Project"),
                context=agent_state.get("context", ""),
                requirements=agent_state.get("requirements", []),
                testCases=agent_state.get("testCases", [])
            )
        
        # Add user message to conversation
        conversation_state["messages"].append(HumanMessage(content=user_message))
        
        # Get streaming response from agent
        try:
            # Add proper configuration for checkpointer
            config = {"configurable": {"thread_id": str(session_id)}}
            stream_response = graph.astream(
                conversation_state,
                config=config,  # type: ignore
                stream_mode="values"
            )
        except Exception as agent_error:
            logger.warning(f"Agent streaming failed: {agent_error}, falling back to simple LLM")
            # Fallback to simple LLM streaming
            messages = [
                SystemMessage(content=load_main_system_prompt()),
                HumanMessage(content=user_message)
            ]
            stream_response = llm.astream(messages)
            
            # Handle simple LLM streaming
            async for chunk in stream_response:
                if hasattr(chunk, 'content') and chunk.content:
                    yield str(chunk.content)
            return
        
        accumulated_content = ""
        async for chunk in stream_response:
            if "messages" in chunk and chunk["messages"]:
                last_message = chunk["messages"][-1]
                if isinstance(last_message, AIMessage):
                    # Extract content delta
                    if hasattr(last_message, 'content') and last_message.content:
                        new_content = str(last_message.content)  # Ensure it's a string
                        if new_content != accumulated_content:
                            delta = new_content[len(accumulated_content):]
                            accumulated_content = new_content
                            if delta:
                                yield delta
        
        # Update session with final agent state
        final_agent_state = {
            "initialized": True,
            "context": conversation_state.get("context", ""),
            "requirements": conversation_state.get("requirements", []),
            "testCases": conversation_state.get("testCases", [])
        }
        
        # Update session in database
        chat_session_crud.update(
            db=db,
            chat_session_id=session_id,
            agent_state=final_agent_state
        )
        
    except Exception as e:
        logger.error(f"Error in agent response stream: {str(e)}")
        yield f"I apologize, but I encountered an error while processing your request: {str(e)}"

async def stream_simple_llm_response(
    user_message: str,
    session_id: uuid.UUID,
    message_sequence_num: int
) -> AsyncGenerator[str, None]:
    """
    Stream response using simple LLM call (fallback option)
    """
    logger.info(f"Starting simple LLM response stream for session {session_id}")
    
    try:
        # Import here to avoid circular imports
        from ai.agents.conversation_agent import llm
        
        # Create a simple conversation with the LLM
        messages = [
            SystemMessage(content=load_main_system_prompt()),
            HumanMessage(content=user_message)
        ]
        
        # Stream response from LLM
        stream_response = llm.astream(messages)
        
        async for chunk in stream_response:
            if hasattr(chunk, 'content') and chunk.content:
                yield str(chunk.content)
                
    except Exception as e:
        logger.error(f"Error in simple LLM response stream: {str(e)}")
        yield f"I apologize, but I encountered an error while processing your request: {str(e)}"

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
        yield f"data: {start_chunk.json()}\n\n"
        
        # Import and use centralized streaming function
        from ai.agents.conversation_agent import stream_agent_response
        
        # Get configuration
        use_agent = session_data.meta_data.get("use_agent", True) if session_data.meta_data else True
        project_name = session_data.meta_data.get("project_name", "Default Project") if session_data.meta_data else "Default Project"
        
        # Stream content using centralized function
        async for content_delta in stream_agent_response(
            session_id=str(session_id),
            user_message=user_message,
            user_message_seq=user_message_seq,
            session_agent_state=session_data.agent_state,
            project_name=project_name,
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
                yield f"data: {content_chunk.json()}\n\n"
                
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

@router.get("/sessions/{session_id}/stream")
async def stream_session_updates(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stream real-time updates for a chat session"""
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
            detail="Not authorized to stream updates for this chat session"
        )
    
    async def generate_updates():
        """Generate session updates"""
        last_check = datetime.now()
        
        while True:
            try:
                # Check for new messages or updates
                recent_messages = chat_message_crud.get_by_chat(
                    db=db, 
                    chat_id=session_id, 
                    skip=0, 
                    limit=10
                )
                
                # Filter messages updated since last check
                new_messages = [
                    msg for msg in recent_messages 
                    if msg.created_at > last_check or (msg.is_streaming and not msg.stream_complete)
                ]
                
                if new_messages:
                    for message in new_messages:
                        update = {
                            "type": "message_update",
                            "session_id": str(session_id),
                            "message": {
                                "sequence_num": message.sequence_num,
                                "content": message.content,
                                "message_type": message.message_type,
                                "status": message.status,
                                "is_streaming": message.is_streaming,
                                "stream_complete": message.stream_complete,
                                "created_at": message.created_at.isoformat()
                            }
                        }
                        yield f"data: {json.dumps(update)}\n\n"
                
                last_check = datetime.now()
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                error_update = {
                    "type": "error",
                    "session_id": str(session_id),
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_update)}\n\n"
                break
    
    return StreamingResponse(
        generate_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/sessions/{session_id}/messages/{sequence_num}/stream")
async def stream_message_updates(
    session_id: uuid.UUID,
    sequence_num: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stream real-time updates for a specific message (useful for monitoring streaming completion)"""
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
            detail="Not authorized to stream updates for this chat session"
        )
    
    async def generate_message_updates():
        """Generate updates for a specific message"""
        while True:
            try:
                message = chat_message_crud.get(db=db, chat_id=session_id, sequence_num=sequence_num)
                if not message:
                    error_update = {
                        "type": "error",
                        "error": "Message not found"
                    }
                    yield f"data: {json.dumps(error_update)}\n\n"
                    break
                
                update = {
                    "type": "message_status",
                    "session_id": str(session_id),
                    "sequence_num": sequence_num,
                    "status": message.status,
                    "is_streaming": message.is_streaming,
                    "stream_complete": message.stream_complete,
                    "content": message.content,
                    "chunk_sequence": message.chunk_sequence,
                    "updated_at": message.created_at.isoformat()
                }
                yield f"data: {json.dumps(update)}\n\n"
                
                # Stop streaming if message is complete
                if message.stream_complete and not message.is_streaming:
                    break
                    
                await asyncio.sleep(0.5)  # Check every 500ms for faster updates
                
            except Exception as e:
                error_update = {
                    "type": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_update)}\n\n"
                break
    
    return StreamingResponse(
        generate_message_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"
        }
    )
