FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y wget unzip && rm -rf /var/lib/apt/lists/*

# Install Qdrant (standalone binary)
RUN wget https://github.com/qdrant/qdrant/releases/download/v1.7.3/qdrant-x86_64-unknown-linux-gnu.tar.gz \
    && tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz \
    && mv qdrant /usr/local/bin/ \
    && rm qdrant-x86_64-unknown-linux-gnu.tar.gz

# Set workdir
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports (FastAPI default: 8000, Qdrant default: 6333)
EXPOSE 8000 6333

# Start Qdrant, initialize DB, then start FastAPI
CMD bash -c "\
    qdrant & \
    sleep 5 && \
    python db_init.py && \
    uvicorn main:app --host 0.0.0.0 --port 8000 \
"
