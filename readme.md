#  Intelligent Document Agent Backend (FastAPI)

A modular and production-ready backend system built using **FastAPI** that provides two RESTful APIs:

1. **File Upload & Vector Storage API**
2. **RAG-based Conversational Agent with Interview Booking**

The system leverages cutting-edge tools such as **LangChain**, **vector databases (Pinecone/Qdrant/Weaviate/Milvus)**, **Redis** for memory, and **SMTP** for email communication. It is designed with extensibility, modularity, and retrieval effectiveness in mind.

---

##  Features

### 1. **Document Ingestion API**
- Upload `.pdf` or `.txt` files.
- Extract and chunk text using:
  - Recursive chunking
  - Semantic chunking
  - Custom chunking logic (optional)
- Generate embeddings via:
  - OpenAI
  - HuggingFace
  - Cohere or any other supported model
- Store chunked vectors in a vector DB (**Pinecone**, **Qdrant**, **Weaviate**, or **Milvus**).
- Store metadata (file name, chunking method, embedding model, etc.) in a relational/NoSQL DB.

### 2. **RAG-Based Agent API (No RetrievalQA)**
- Implemented using **LangChain**
- Utilizes Redis.
- Maintains conversation history across sessions.
- Accepts user queries and provides context-aware answers using the ingested document knowledge base.
- The RAG query format is as follows: 
   {
  "message": "string",
  "session_id": "string",
  "use_rag": true,
  "max_tokens": 500,
  "collection_name": "string"
}
- The collection name of the uploaded file could be found in http://localhost:6333/collections

### 3. **Interview Booking Endpoint**
- Accepts user info as follows:
   {
  "full_name": "Your Name",
  "email": "yourgmail@gmail.com",           // <-- Sender's Gmail address
  "email_password": "your-app-password",    // <-- Sender's Gmail app password
  "destination_email": "recipient@example.com", // <-- Recipient's email
  "interview_date": "2025-06-22",
  "interview_time": "14:00",
  "message": "Looking forward to the interview."
}
- Stores booking in a database.
- Sends confirmation via SMTP to the owner/admin email.

---

##  Tech Stack

| Component         | Technology                |
|------------------|---------------------------|
| Framework        | FastAPI                   |
| Embeddings       | HuggingFace               |
| Chunking Methods | Recursive / Semantic / Custom |
| Vector DB        | Qdrant                    |
| Memory Layer     | Redis                     |
| Storage DB       | sqllite                   |
| Agent Framework  | LangChain                 |
| Email Service    | SMTP                      |

##  API Overview

### `/api/v1/files/upload`
- **Method:** POST
- **Description:** Upload a `.pdf` or `.txt` file for processing and storage.
- **Payload:** Multipart/form-data (`file`, `chunking_method`, `embedding_model`)
- **Response:** JSON with file metadata, processing status, and chunking/embedding method.

### `/api/v1/files/status/{file_id}`
- **Method:** GET
- **Description:** Get processing status and metadata for an uploaded file.
- **Response:** JSON with file status, chunk count, processing/embedding times, and errors if any.

### `/api/v1/files/files`
- **Method:** GET
- **Description:** List all uploaded files, optionally filtered by status.
- **Response:** JSON with a list of files and their metadata.

### `/api/v1/files/files/{file_id}`
- **Method:** DELETE
- **Description:** Delete a file and all associated data (vectors, chunks, metadata).
- **Response:** JSON message confirming deletion.

### `/api/v1/files/performance/embeddings`
- **Method:** GET
- **Description:** Get cached performance metrics for different embedding models and chunking methods.
- **Response:** JSON with model/method performance stats.

### `/api/v1/files/performance/{file_id}`
- **Method:** GET
- **Description:** Get actual chunking and embedding performance for a specific uploaded file.
- **Response:** JSON with file-specific performance metrics.

### `/api/v1/rag/chat`
- **Method:** POST
- **Description:** Chat with the RAG agent. Maintains session context and can use RAG over uploaded documents.
- **Payload:** 
  ```json
  {
    "message": "string",
    "session_id": "string (optional)",
    "use_rag": true,
    "max_tokens": 500,
    "collection_name": "string (optional)"
  }
  ```
- **Response:** JSON with agent response, session ID, sources, tools used, and response time.

### `/api/v1/rag/book-interview`
- **Method:** POST
- **Description:** Book an interview with the agent's assistance.
- **Payload:** 
  ```json
  {
    "full_name": "Your Name",
    "email": "yourgmail@gmail.com",
    "email_password": "your-app-password",
    "destination_email": "recipient@example.com",
    "interview_date": "YYYY-MM-DD",
    "interview_time": "HH:MM",
    "message": "Looking forward to the interview."
  }
  ```
- **Response:** JSON with booking ID, status, message, and confirmation status.

---

##  How to Run (Step by Step)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Fast_Backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *(Create requirements.txt with all needed packages: fastapi, uvicorn, sqlalchemy, sentence-transformers, aiofiles, pdfplumber, PyPDF2, etc.)*

4. **Copy and configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

5. **Initialize the database**
   ```bash
   python -c "from database.models import init_db; init_db()"
   ```
6. **Start Qdrant**
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

6. **Run the FastAPI server**
   ```bash
   uvicorn main:app --reload
   ```

7. **Access the API docs**
   - Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

---
 
 ** I have made it easier by creating a dockerfile. You can just create an image **
 
 ##  Experimental Findings

### 🔹 Chunking & Embedding Evaluation

| Chunking Method | Embedding Model        | Retrieval Accuracy | Latency (s) | Memory Usage |
|-----------------|-----------------------|-------------------|-------------|-------------|
| Recursive       | all-MiniLM-L6-v2      | 82%               | 0.15        | low         |
| Semantic        | all-mpnet-base-v2     | 89%               | 0.45        | medium      |

> **Findings:**  
> - The **semantic chunking** method combined with the **all-mpnet-base-v2** embedding model achieved the highest retrieval accuracy (89%), though with higher latency (0.45s) and medium memory usage.
> - The **recursive chunking** method with **all-MiniLM-L6-v2** provided lower latency (0.15s) and low memory usage, but slightly lower retrieval accuracy (82%).
> - For applications where speed and resource efficiency are critical, recursive chunking with all-MiniLM-L6-v2 is recommended.
> - For maximum retrieval accuracy, semantic chunking with all-mpnet-base-v2 is preferred, accepting a moderate increase in latency and memory usage.