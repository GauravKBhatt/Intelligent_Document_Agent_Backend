# api/rag_agent.py - RAG Agent API with LangChain Integration
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json

from database.models import get_db, ConversationHistory, InterviewBooking
from services.rag_agent_service import RAGAgentService
from services.memory_service import MemoryService
from services.email_service import EmailService
from config.settings import settings

router = APIRouter()

# Initialize services
rag_service = RAGAgentService()
memory_service = MemoryService()
email_service = EmailService()

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_rag: bool = True
    max_tokens: int = 500

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[Dict[str, Any]]
    tools_used: List[str]
    response_time: float

class InterviewBookingRequest(BaseModel):
    full_name: str
    email: EmailStr
    interview_date: str  # YYYY-MM-DD format
    interview_time: str  # HH:MM format
    message: Optional[str] = None

class InterviewBookingResponse(BaseModel):
    booking_id: int
    status: str
    message: str
    confirmation_sent: bool

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Chat with the RAG agent
    
    The agent can:
    - Answer questions using RAG from uploaded documents
    - Book interviews
    - Use various tools to help users
    - Maintain conversation context
    """
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        import time
        start_time = time.time()
        
        # Get conversation history from memory
        conversation_history = await memory_service.get_conversation_history(session_id)
        
        # Process the message with the RAG agent
        agent_response = await rag_service.process_message(
            message=request.message,
            session_id=session_id,
            conversation_history=conversation_history,
            use_rag=request.use_rag,
            max_tokens=request.max_tokens
        )
        
        response_time = time.time() - start_time
        
        # Save conversation to memory and database
        background_tasks.add_task(
            save_conversation,
            session_id,
            request.message,
            agent_response,
            response_time,
            db
        )
        
        return ChatResponse(
            response=agent_response['response'],
            session_id=session_id,
            sources=agent_response.get('sources', []),
            tools_used=agent_response.get('tools_used', []),
            response_time=response_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

async def save_conversation(
    session_id: str,
    user_message: str,
    agent_response: Dict[str, Any],
    response_time: float,
    db: Session
):
    """Background task to save conversation"""
    try:
        # Save to memory service
        await memory_service.add_to_conversation_history(
            session_id,
            user_message,
            agent_response['response']
        )
        
        # Save to database
        conversation_record = ConversationHistory(
            session_id=session_id,
            user_message=user_message,
            agent_response=agent_response['response'],
            tools_used=agent_response.get('tools_used', []),
            retrieval_context=agent_response.get('sources', []),
            response_time=response_time
        )
        
        db.add(conversation_record)
        db.commit()
        
    except Exception as e:
        print(f"Error saving conversation: {str(e)}")

@router.post("/book-interview", response_model=InterviewBookingResponse)
async def book_interview(
    request: InterviewBookingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Book an interview with the agent's assistance
    """
    try:
        # Create booking record
        booking = InterviewBooking(
            full_name=request.full_name,
            email=request.email,
            interview_date=request.interview_date,
            interview_time=request.interview_time,
            message=request.message,
            status="pending"
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)

        # Send confirmation email in background
        subject = "Interview Booking Confirmation"
        body = f"Dear {request.full_name},\n\nYour interview is booked for {request.interview_date} at {request.interview_time}."
        background_tasks.add_task(
            email_service.send_confirmation,
            to_email=settings.ADMIN_EMAIL,
            subject=subject,
            body=body
        )

        return InterviewBookingResponse(
            booking_id=booking.id,
            status="success",
            message="Interview booked successfully.",
            confirmation_sent=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error booking interview: {str(e)}")