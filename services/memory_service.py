# services/memory_service.py - Memory Service Stub
class MemoryService:
    async def get_conversation_history(self, session_id):
        # Return empty history for now
        return []

    async def add_to_conversation_history(self, session_id, user_message, agent_response):
        # No-op for now
        pass
