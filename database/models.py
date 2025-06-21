from config.settings import settings
print("DEBUG: settings.DATABASE_URL =", settings.DATABASE_URL)

# database/models.py - SQLAlchemy models and DB init
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from datetime import datetime
import os

Base = declarative_base()

class FileMetadata(Base):
    __tablename__ = "file_metadata"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    original_filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    file_type = Column(String)
    chunking_method = Column(String)
    embedding_model = Column(String)
    processing_status = Column(String, default="pending")
    chunk_count = Column(Integer, default=0)
    vector_collection_id = Column(String, nullable=True)
    processing_time = Column(Float, nullable=True)
    embedding_time = Column(Float, nullable=True)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)
    # Relationship
    chunks = relationship("TextChunk", back_populates="file")

class TextChunk(Base):
    __tablename__ = "text_chunk"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_metadata.id"))
    chunk_index = Column(Integer)
    content = Column(Text)
    chunk_size = Column(Integer)
    vector_id = Column(String)
    file = relationship("FileMetadata", back_populates="chunks")

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_message = Column(Text)
    agent_response = Column(Text)
    tools_used = Column(JSON)
    retrieval_context = Column(JSON)
    response_time = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class InterviewBooking(Base):
    __tablename__ = "interview_booking"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String)
    interview_date = Column(String)
    interview_time = Column(String)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")

from config.settings import settings
from sqlalchemy import create_engine

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
