# services/rag_agent_service.py - Actual RAG retrieval logic
from services.vector_store import VectorStoreService
from database.models import FileMetadata

class RAGAgentService:
    def __init__(self):
        self.vector_store = VectorStoreService()

    async def process_message(self, message, session_id, conversation_history, use_rag, max_tokens, file_id=None):
        # Retrieve relevant chunks for the specified file_id
        if file_id:
            collection_id = f"file_{file_id}"  # This should match your collection naming in file processing
            relevant_chunks = self.vector_store.search(collection_id, message)
        else:
            relevant_chunks = []  # Optionally, search all collections

        # Simple answer generation: concatenate relevant chunks as context
        context = "\n".join([chunk['content'] for chunk in relevant_chunks]) if relevant_chunks else "No relevant context found."
        answer = f"Context:\n{context}\n\nAnswer: {self.simple_answer(message, context)}"
        return {
            "response": answer,
            "sources": relevant_chunks,
            "tools_used": ["vector_search"],
        }

    def simple_answer(self, question, context):
        # Placeholder: In production, call your LLM here
        if context and context != "No relevant context found.":
            return f"Based on the document: {context[:200]}..."
        else:
            return "Sorry, I could not find relevant information in the uploaded document."
