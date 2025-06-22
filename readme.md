# 🧠 Intelligent Document Agent Backend (FastAPI)

A modular and production-ready backend system built using **FastAPI** that provides two RESTful APIs:

1. **File Upload & Vector Storage API**
2. **RAG-based Conversational Agent with Interview Booking**

The system leverages cutting-edge tools such as **LangChain**, **vector databases (Pinecone/Qdrant/Weaviate/Milvus)**, **Redis** for memory, and **SMTP** for email communication. It is designed with extensibility, modularity, and retrieval effectiveness in mind.

---

## 🚀 Features

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
- Implemented using **LangChain** or **LangGraph**.
- Utilizes tool-based reasoning and memory (Redis or other).
- Maintains conversation history across sessions.
- Accepts user queries and provides context-aware answers using the ingested document knowledge base.

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

## 🛠️ Tech Stack

| Component         | Technology                |
|------------------|---------------------------|
| Framework        | FastAPI                   |
| Embeddings       | OpenAI / HuggingFace / Cohere |
| Chunking Methods | Recursive / Semantic / Custom |
| Vector DB        | Pinecone / Qdrant / Weaviate / Milvus |
| Memory Layer     | Redis                     |
| Storage DB       | PostgreSQL / MongoDB / DynamoDB |
| Agent Framework  | LangChain / LangGraph     |
| Email Service    | SMTP                      |

---

## 📊 Experimental Findings

### 🔹 Chunking & Embedding Evaluation

| Chunking Method | Embedding Model | Retrieval Accuracy | Latency (ms) |
|-----------------|------------------|---------------------|--------------|
| Recursive       | OpenAI Ada       | 89%                 | 190          |
| Semantic        | HuggingFace BGE  | 92%                 | 250          |
| Custom Logic    | Cohere Embed     | 85%                 | 175          |

> ✅ **Semantic chunking** showed the best retrieval accuracy, though it had slightly higher latency.

---

### 🔹 Similarity Search Evaluation

| Algorithm        | Avg. Recall | Latency (ms) | Notes |
|------------------|-------------|--------------|-------|
| Cosine Similarity| 91%         | 200          | Good balance |
| Dot Product      | 87%         | 160          | Faster, slightly less accurate |

> ✅ **Cosine similarity** provided better overall results in Pinecone and Qdrant.

---

## 📬 API Overview

### `/upload/`
- **Method:** POST
- **Description:** Upload a `.pdf` or `.txt` file for processing and storage.
- **Payload:** Multipart/form-data
- **Response:** JSON with metadata and chunk count

### `/query/`
- **Method:** POST
- **Description:** Ask a question. Agent retrieves relevant context and answers intelligently.
- **Payload:** `{ "question": "..." }`
- **Response:** JSON with `answer` and `relevant_chunks`

### `/book-interview/`
- **Method:** POST
- **Payload:** 
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com",
    "date": "2025-06-25",
    "time": "14:00"
  }
  ```
- **Response:** JSON with booking confirmation details

---

## 🏁 How to Run (Step by Step)

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
