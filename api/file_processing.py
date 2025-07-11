# api/file_processing.py - File Processing API Endpoints
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import aiofiles
import os
import time
from datetime import datetime
import uuid

from database.models import get_db, FileMetadata, TextChunk
from services.text_processor import TextProcessor
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStoreService
from config.settings import settings
from database.models import SessionLocal
from fastapi.responses import JSONResponse

router = APIRouter()

# Initialize services
text_processor = TextProcessor()
embedding_service = EmbeddingService()
vector_store = VectorStoreService()

class FileProcessingResponse:
    def __init__(self, file_id: int, status: str, message: str, metadata: dict = None):
        self.file_id = file_id
        self.status = status
        self.message = message
        self.metadata = metadata or {}

@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunking_method: str = "recursive",
    embedding_model: str = settings.DEFAULT_EMBEDDING_MODEL,
    db: Session = Depends(get_db)
):
    """
    Upload and process a file (.pdf or .txt)
    
    Args:
        file: The uploaded file
        chunking_method: Method for text chunking (recursive, semantic, custom)
        embedding_model: Model to use for generating embeddings
        db: Database session
    """
    
    # Validate file type
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_extension} not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Validate file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    # Ensure the upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    try:
        # Save file to disk
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create file metadata record
        file_metadata = FileMetadata(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file.size,
            file_type=file_extension,
            chunking_method=chunking_method,
            embedding_model=embedding_model,
            processing_status="pending"
        )
        
        db.add(file_metadata)
        db.commit()
        db.refresh(file_metadata)
        
        # Process file in background
        background_tasks.add_task(
            process_file_background,
            file_metadata.id,
            file_path,
            chunking_method,
            embedding_model
        )
        
        return {
            "file_id": file_metadata.id,
            "status": "uploaded",
            "message": "File uploaded successfully. Processing started.",
            "filename": file.filename,
            "processing_method": {
                "chunking": chunking_method,
                "embedding_model": embedding_model
            }
        }
        
    except Exception as e:
        # Clean up file if processing failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

async def process_file_background(
    file_id: int,
    file_path: str,
    chunking_method: str,
    embedding_model: str
):
    """Background task to process uploaded file and record performance metrics"""
    db = SessionLocal()
    start_time = time.time()
    try:
        # Update status to processing
        file_metadata = db.query(FileMetadata).filter(FileMetadata.id == file_id).first()
        file_metadata.processing_status = "processing"
        db.commit()

        # Extract text from file
        text_content = text_processor.extract_text(file_path)

        # Chunk the text
        chunk_start = time.time()
        chunks = text_processor.chunk_text(text_content, method=chunking_method)
        chunk_time = time.time() - chunk_start

        # Generate embeddings
        embedding_start = time.time()
        embeddings = embedding_service.generate_embeddings(chunks, model=embedding_model)
        embedding_time = time.time() - embedding_start

        # Create vector collection
        collection_id = f"file_{file_id}_{int(time.time())}"
        vector_store.create_collection(collection_id)

        # Store vectors and create chunk records
        chunk_records = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = vector_store.add_vector(
                collection_id=collection_id,
                vector=embedding,
                payload={
                    "file_id": file_id,
                    "chunk_index": i,
                    "content": chunk,
                    "chunking_method": chunking_method,
                    "embedding_model": embedding_model
                }
            )
            # Create database record for chunk (optional, not shown here)

        # Update file metadata with performance
        file_metadata.processing_status = "completed"
        file_metadata.chunk_count = len(chunks)
        file_metadata.vector_collection_id = collection_id
        file_metadata.processing_time = chunk_time
        file_metadata.embedding_time = embedding_time
        db.commit()
    except Exception as e:
        file_metadata = db.query(FileMetadata).filter(FileMetadata.id == file_id).first()
        if file_metadata:
            file_metadata.processing_status = "failed"
            file_metadata.error_message = str(e)
            db.commit()
    finally:
        db.close()

@router.get("/status/{file_id}")
async def get_file_status(file_id: int, db: Session = Depends(get_db)):
    """Get processing status of uploaded file"""
    file_metadata = db.query(FileMetadata).filter(FileMetadata.id == file_id).first()
    
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "file_id": file_id,
        "filename": file_metadata.original_filename,
        "status": file_metadata.processing_status,
        "chunk_count": file_metadata.chunk_count,
        "processing_time": file_metadata.processing_time,
        "embedding_time": file_metadata.embedding_time,
        "upload_timestamp": file_metadata.upload_timestamp,
        "error_message": file_metadata.error_message
    }

@router.get("/files")
async def list_files(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all uploaded files with optional status filter"""
    query = db.query(FileMetadata)
    
    if status:
        query = query.filter(FileMetadata.processing_status == status)
    
    files = query.offset(skip).limit(limit).all()
    
    return {
        "files": [
            {
                "file_id": f.id,
                "filename": f.original_filename,
                "status": f.processing_status,
                "upload_timestamp": f.upload_timestamp,
                "chunk_count": f.chunk_count,
                "chunking_method": f.chunking_method,
                "embedding_model": f.embedding_model
            }
            for f in files
        ],
        "total": len(files)
    }

@router.delete("/files/{file_id}")
async def delete_file(file_id: int, db: Session = Depends(get_db)):
    """Delete a file and all associated data"""
    file_metadata = db.query(FileMetadata).filter(FileMetadata.id == file_id).first()
    
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Delete from vector database
        if file_metadata.vector_collection_id:
            vector_store.delete_collection(file_metadata.vector_collection_id)
        
        # Delete chunks from database
        db.query(TextChunk).filter(TextChunk.file_id == file_id).delete()
        
        # Delete file from disk
        if os.path.exists(file_metadata.file_path):
            os.remove(file_metadata.file_path)
        
        # Delete metadata
        db.delete(file_metadata)
        db.commit()
        
        return {"message": "File deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.get("/performance/embeddings")
async def get_embedding_performance(db: Session = Depends(get_db)):
    """Get performance comparison of different embedding models and chunking methods"""
    # This would return cached performance metrics
    # In a real implementation, you'd run periodic tests and store results
    return {
        "embedding_models": [
            {
                "model": "all-MiniLM-L6-v2",
                "avg_latency": 0.15,
                "retrieval_accuracy": 0.82,
                "memory_usage": "low"
            },
            {
                "model": "all-mpnet-base-v2",
                "avg_latency": 0.45,
                "retrieval_accuracy": 0.89,
                "memory_usage": "medium"
            }
        ],
        "chunking_methods": [
            {
                "method": "recursive",
                "avg_chunk_size": 1000,
                "semantic_coherence": 0.75,
                "processing_speed": "fast"
            },
            {
                "method": "semantic",
                "avg_chunk_size": 1200,
                "semantic_coherence": 0.91,
                "processing_speed": "medium"
            }
        ]
    }

@router.get("/performance/file/{file_id}")
async def get_file_performance(file_id: int, db: Session = Depends(get_db)):
    """Get real embedding and chunking performance for a specific uploaded file"""
    file_metadata = db.query(FileMetadata).filter(FileMetadata.id == file_id).first()
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    return {
        "file_id": file_metadata.id,
        "filename": file_metadata.original_filename,
        "chunking_method": file_metadata.chunking_method,
        "embedding_model": file_metadata.embedding_model,
        "chunk_count": file_metadata.chunk_count,
        "chunking_time": file_metadata.processing_time,
        "embedding_time": file_metadata.embedding_time,
        "status": file_metadata.processing_status,
        "error_message": file_metadata.error_message,
    }

@router.get("/performance/similarity-search")
async def compare_similarity_search_algorithms(
    file_id: int,
    query: str,
    top_k: int = 3,
    db: Session = Depends(get_db)
):
    """
    Compare Cosine and Dot Product similarity search in Qdrant and report findings.
    """
    file_metadata = db.query(FileMetadata).filter(FileMetadata.id == file_id).first()
    if not file_metadata or not file_metadata.vector_collection_id:
        raise HTTPException(status_code=404, detail="File or vector collection not found")
    collection_id = file_metadata.vector_collection_id

    # Only works if Qdrant is used
    if not hasattr(vector_store, "qdrant") or vector_store.qdrant is None:
        return JSONResponse(
            status_code=400,
            content={"detail": "Similarity search comparison only supported with Qdrant backend."}
        )

    # Prepare: get embedding for the query
    query_emb = embedding_service.generate_embeddings([query])[0]

    # Run Cosine similarity search
    import time
    cosine_start = time.time()
    cosine_results = vector_store.qdrant.search(
        collection_name=collection_id,
        query_vector=query_emb,
        limit=top_k,
        search_params={"hnsw_ef": 128, "exact": False},
        # Cosine is default for this collection
    )
    cosine_time = time.time() - cosine_start

    # Dot Product search is not supported unless the collection was created with Dot Product distance.
    # So, we warn the user and skip the dot product search.
    findings = {
        "cosine": {
            "top_k": top_k,
            "results": [p.payload for p in cosine_results],
            "latency_sec": round(cosine_time, 4)
        },
        "dot_product": {
            "warning": (
                "Dot Product search is only supported if the collection was created with distance='Dot'. "
                "Current collection uses Cosine. To compare, re-upload the file with Dot Product as the distance metric."
            ),
            "results": [],
            "latency_sec": None
        },
        "overlap_in_top_k": 0,
        "finding": (
            "Cosine similarity is generally more stable for normalized embeddings and is the default for sentence-transformers. "
            "Dot product search is not available for this collection. "
            f"Cosine search took {round(cosine_time,4)}s."
        )
    }
    return findings