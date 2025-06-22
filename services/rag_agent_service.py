# services/rag_agent_service.py - Actual RAG retrieval logic
from services.vector_store import VectorStoreService
import os

class RAGAgentService:
    def __init__(self):
        self.vector_store = VectorStoreService()

    async def process_message(self, message, session_id, conversation_history, use_rag, max_tokens, collection_name=None):
        # Retrieve relevant chunks for the specified collection_name
        relevant_chunks = []
        if collection_name:
            try:
                relevant_chunks = self.vector_store.search(collection_name, message)
            except Exception as e:
                # Handle missing collection or other vector store errors gracefully
                if "doesn't exist" in str(e) or "Not found" in str(e):
                    return {
                        "response": "Sorry, I could not find the uploaded document or its data. Please ensure the file is processed and available.",
                        "sources": [],
                        "tools_used": ["vector_search"],
                    }
                else:
                    return {
                        "response": f"An error occurred while searching the document: {str(e)}",
                        "sources": [],
                        "tools_used": ["vector_search"],
                    }
        # Simple answer generation: concatenate relevant chunks as context
        if relevant_chunks:
            context = "\n".join([chunk['content'] for chunk in relevant_chunks])
            answer = self.simple_answer(message, context)
        else:
            context = "No relevant context found."
            answer = "Sorry, I could not find relevant information in the uploaded document."

        return {
            "response": f"Context:\n{context}\n\nAnswer: {answer}",
            "sources": relevant_chunks,
            "tools_used": ["vector_search"],
        }

    def simple_answer(self, question, context):
        # Very basic RAG logic: return the most relevant sentence from the context
        if not context or context == "No relevant context found.":
            return "Sorry, I could not find relevant information in the uploaded document."
        # Split context into sentences and return the one with the most keyword overlap
        import re
        sentences = re.split(r'(?<=[.!?]) +', context)
        question_words = set(question.lower().split())
        best_sentence = ""
        best_score = 0
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            score = len(question_words & sentence_words)
            if score > best_score:
                best_score = score
                best_sentence = sentence
        if best_sentence:
            return best_sentence.strip()
        else:
            return context[:200] + "..." if len(context) > 200 else context
