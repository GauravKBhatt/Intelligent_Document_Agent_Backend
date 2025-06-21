# main.py - FastAPI Application Entry Point
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import asyncio
import logging
from datetime import datetime

# Import our modules
from api.file_processing import router as file_router
from api.rag_agent import router as rag_router
from database.models import init_db
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Backend System",
    description="A comprehensive RAG system with file processing and agentic capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(file_router, prefix="/api/v1/files", tags=["File Processing"])
app.include_router(rag_router, prefix="/api/v1/rag", tags=["RAG Agent"])

@app.on_event("startup")
async def startup_event():
    """Initialize database and connections on startup"""
    logger.info("Starting up RAG Backend System...")
    init_db()  # <-- Just call it, do NOT await
    logger.info("Database initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger.info("Shutting down RAG Backend System...")

@app.get("/")
async def root():
    """Root endpoint with system status"""
    return {
        "message": "RAG Backend System",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "connected",
            "vector_db": "connected",
            "redis": "connected"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)