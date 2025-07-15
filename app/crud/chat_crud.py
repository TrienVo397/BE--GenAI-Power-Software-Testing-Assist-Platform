# c:\Users\dorem\Documents\GitHub\BE--GenAI-Power-Software-Testing-Assist-Platform\app\crud\chat_crud.py
from typing import List, Optional, Sequence
from sqlmodel import Session, select, and_, desc, asc
from datetime import datetime, timezone
import uuid
import logging

from app.models.chat import ChatSession, ChatMessage
from langchain_core.messages import AnyMessage

class CRUDChatSession:
    def create(self, db: Session, **kwargs) -> ChatSession:
        """Create a new chat session."""
        db_chat_session = ChatSession(**kwargs)
        db.add(db_chat_session)
        db.commit()
        db.refresh(db_chat_session)
        
        logging.info(f"Chat session created: {db_chat_session.id}")
        return db_chat_session

    def get(self, db: Session, chat_session_id: uuid.UUID) -> Optional[ChatSession]:
        """Get a chat session by ID."""
        statement = select(ChatSession).where(ChatSession.id == chat_session_id)
        chat_session = db.exec(statement).first()
        return chat_session

    def get_by_user(self, db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ChatSession]:
        """Get chat sessions by user ID."""
        statement = select(ChatSession).where(ChatSession.user_id == user_id).offset(skip).limit(limit).order_by(desc(ChatSession.updated_at))
        chat_sessions = db.exec(statement).all()
        return list(chat_sessions)

    def get_by_project(self, db: Session, project_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ChatSession]:
        """Get chat sessions by project ID."""
        statement = select(ChatSession).where(ChatSession.project_id == project_id).offset(skip).limit(limit).order_by(desc(ChatSession.updated_at))
        chat_sessions = db.exec(statement).all()
        return list(chat_sessions)

    def get_by_user_and_project(self, db: Session, user_id: uuid.UUID, project_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ChatSession]:
        """Get chat sessions by user ID and project ID."""
        statement = select(ChatSession).where(
            and_(ChatSession.user_id == user_id, ChatSession.project_id == project_id)
        ).offset(skip).limit(limit).order_by(desc(ChatSession.updated_at))
        chat_sessions = db.exec(statement).all()
        return list(chat_sessions)

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[ChatSession]:
        """Get multiple chat sessions."""
        statement = select(ChatSession).offset(skip).limit(limit).order_by(desc(ChatSession.updated_at))
        chat_sessions = db.exec(statement).all()
        return list(chat_sessions)

    def update(self, db: Session, chat_session_id: uuid.UUID, **kwargs) -> Optional[ChatSession]:
        """Update a chat session."""
        statement = select(ChatSession).where(ChatSession.id == chat_session_id)
        db_chat_session = db.exec(statement).first()
        if db_chat_session:
            # Update chat session attributes
            for key, value in kwargs.items():
                if hasattr(db_chat_session, key):
                    setattr(db_chat_session, key, value)
            
            # Update the updated_at timestamp
            db_chat_session.updated_at = datetime.now(timezone.utc)
            
            db.add(db_chat_session)
            db.commit()
            db.refresh(db_chat_session)
            
            logging.info(f"Chat session updated: {db_chat_session.id}")
            return db_chat_session
        return None

    def delete(self, db: Session, chat_session_id: uuid.UUID) -> Optional[ChatSession]:
        """Delete a chat session and all its messages."""
        statement = select(ChatSession).where(ChatSession.id == chat_session_id)
        chat_session = db.exec(statement).first()
        if chat_session:
            # Delete all messages first (cascade should handle this, but being explicit)
            message_statement = select(ChatMessage).where(ChatMessage.chat_id == chat_session_id)
            messages = db.exec(message_statement).all()
            for message in messages:
                db.delete(message)
            
            # Delete the chat session
            db.delete(chat_session)
            db.commit()
            
            logging.info(f"Chat session deleted: {chat_session_id}")
            return chat_session
        return None

    def add_langchain_message(self, db: Session, chat_session_id: uuid.UUID, message: AnyMessage) -> Optional[ChatMessage]:
        """Add a LangChain message to a chat session."""
        # Get the chat session
        chat_session = self.get(db, chat_session_id)
        if not chat_session:
            return None
        
        # Convert LangChain message to ChatMessage
        chat_message = chat_session.add_langchain_message(message)
        
        # Get the next sequence number (this also updates the chat session)
        next_seq = self.get_next_sequence_number(db, chat_session_id)
        chat_message.sequence_num = next_seq
        
        # Save to database
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        
        return chat_message

    def get_next_sequence_number(self, db: Session, chat_session_id: uuid.UUID) -> int:
        """Get the next sequence number for a new message in a chat session."""
        # Get the current sequence number from the chat session
        chat_session = self.get(db, chat_session_id)
        if chat_session:
            next_seq = chat_session.current_message_sequence_num + 1
            # Update the chat session's current sequence number
            chat_session.current_message_sequence_num = next_seq
            chat_session.updated_at = datetime.now(timezone.utc)
            db.add(chat_session)
            db.commit()
            return next_seq
        return 0


class CRUDChatMessage:
    def create(self, db: Session, **kwargs) -> ChatMessage:
        """Create a new chat message."""
        # Get the next sequence number if not provided
        if 'sequence_num' not in kwargs:
            kwargs['sequence_num'] = chat_session_crud.get_next_sequence_number(db, kwargs['chat_id'])
        
        db_chat_message = ChatMessage(**kwargs)
        db.add(db_chat_message)
        db.commit()
        db.refresh(db_chat_message)
        
        # Note: The chat session's current_message_sequence_num is already updated in get_next_sequence_number
        # So we don't need to update it again here
        
        logging.info(f"Chat message created: {db_chat_message.sequence_num} in chat {db_chat_message.chat_id}")
        return db_chat_message

    def get(self, db: Session, chat_id: uuid.UUID, sequence_num: int) -> Optional[ChatMessage]:
        """Get a chat message by chat_id and sequence_num."""
        statement = select(ChatMessage).where(
            and_(ChatMessage.chat_id == chat_id, ChatMessage.sequence_num == sequence_num)
        )
        chat_message = db.exec(statement).first()
        return chat_message

    def get_by_chat(self, db: Session, chat_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ChatMessage]:
        """Get chat messages by chat ID."""
        statement = select(ChatMessage).where(ChatMessage.chat_id == chat_id).offset(skip).limit(limit).order_by(asc(ChatMessage.sequence_num))
        chat_messages = db.exec(statement).all()
        return list(chat_messages)

    def get_latest_messages(self, db: Session, chat_id: uuid.UUID, limit: int = 10) -> List[ChatMessage]:
        """Get the latest messages from a chat session."""
        statement = select(ChatMessage).where(ChatMessage.chat_id == chat_id).order_by(desc(ChatMessage.sequence_num)).limit(limit)
        chat_messages = db.exec(statement).all()
        return list(reversed(chat_messages))  # Return in chronological order

    def get_streaming_messages(self, db: Session, chat_id: uuid.UUID) -> List[ChatMessage]:
        """Get all streaming messages from a chat session."""
        statement = select(ChatMessage).where(
            and_(ChatMessage.chat_id == chat_id, ChatMessage.is_streaming == True)
        ).order_by(asc(ChatMessage.sequence_num))
        chat_messages = db.exec(statement).all()
        return list(chat_messages)

    def get_by_status(self, db: Session, chat_id: uuid.UUID, status: str) -> List[ChatMessage]:
        """Get chat messages by status."""
        statement = select(ChatMessage).where(
            and_(ChatMessage.chat_id == chat_id, ChatMessage.status == status)
        ).order_by(asc(ChatMessage.sequence_num))
        chat_messages = db.exec(statement).all()
        return list(chat_messages)

    def update(self, db: Session, chat_id: uuid.UUID, sequence_num: int, **kwargs) -> Optional[ChatMessage]:
        """Update a chat message."""
        statement = select(ChatMessage).where(
            and_(ChatMessage.chat_id == chat_id, ChatMessage.sequence_num == sequence_num)
        )
        db_chat_message = db.exec(statement).first()
        if db_chat_message:
            # Update chat message attributes
            for key, value in kwargs.items():
                if hasattr(db_chat_message, key):
                    setattr(db_chat_message, key, value)
            
            db.add(db_chat_message)
            db.commit()
            db.refresh(db_chat_message)
            
            # Update chat session's updated_at
            chat_session_statement = select(ChatSession).where(ChatSession.id == chat_id)
            chat_session = db.exec(chat_session_statement).first()
            if chat_session:
                chat_session.updated_at = datetime.now(timezone.utc)
                db.add(chat_session)
                db.commit()
            
            logging.info(f"Chat message updated: {db_chat_message.sequence_num} in chat {db_chat_message.chat_id}")
            return db_chat_message
        return None

    def delete(self, db: Session, chat_id: uuid.UUID, sequence_num: int) -> Optional[ChatMessage]:
        """Delete a chat message."""
        statement = select(ChatMessage).where(
            and_(ChatMessage.chat_id == chat_id, ChatMessage.sequence_num == sequence_num)
        )
        chat_message = db.exec(statement).first()
        if chat_message:
            db.delete(chat_message)
            db.commit()
            
            # Update chat session's updated_at
            chat_session_statement = select(ChatSession).where(ChatSession.id == chat_id)
            chat_session = db.exec(chat_session_statement).first()
            if chat_session:
                chat_session.updated_at = datetime.now(timezone.utc)
                db.add(chat_session)
                db.commit()
            
            logging.info(f"Chat message deleted: {sequence_num} in chat {chat_id}")
            return chat_message
        return None

    def mark_streaming_complete(self, db: Session, chat_id: uuid.UUID, sequence_num: int) -> Optional[ChatMessage]:
        """Mark a streaming message as complete."""
        chat_message = self.get(db, chat_id, sequence_num)
        if chat_message:
            chat_message.is_streaming = False
            chat_message.stream_complete = True
            chat_message.status = "complete"
            
            db.add(chat_message)
            db.commit()
            db.refresh(chat_message)
            
            logging.info(f"Streaming completed for message: {sequence_num} in chat {chat_id}")
            return chat_message
        return None

    def update_status(self, db: Session, chat_id: uuid.UUID, sequence_num: int, status: str, status_details: Optional[str] = None) -> Optional[ChatMessage]:
        """Update the status of a chat message."""
        chat_message = self.get(db, chat_id, sequence_num)
        if chat_message:
            chat_message.status = status
            if status_details:
                chat_message.status_details = status_details
            
            db.add(chat_message)
            db.commit()
            db.refresh(chat_message)
            
            logging.info(f"Status updated for message: {sequence_num} in chat {chat_id} to {status}")
            return chat_message
        return None


# Create instances of the CRUD classes
chat_session_crud = CRUDChatSession()
chat_message_crud = CRUDChatMessage()
