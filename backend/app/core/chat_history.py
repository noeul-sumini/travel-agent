from typing import List, Dict, Any
import json
import redis
from app.core.config import settings

class ChatHistoryManager:
    """Manages chat history using Redis."""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.history_ttl = 3600 * 24 * 7  # 7 days
    
    def _get_history_key(self, session_id: str) -> str:
        """Get Redis key for chat history."""
        return f"chat_history:{session_id}"
    
    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session."""
        history_key = self._get_history_key(session_id)
        history_data = self.redis_client.get(history_key)
        if history_data:
            return json.loads(history_data)
        return []
    
    def add_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """Add a message to chat history."""
        history_key = self._get_history_key(session_id)
        history = self.get_history(session_id)
        history.append(message)
        self.redis_client.setex(
            history_key,
            self.history_ttl,
            json.dumps(history)
        )
    
    def clear_history(self, session_id: str) -> None:
        """Clear chat history for a session."""
        history_key = self._get_history_key(session_id)
        self.redis_client.delete(history_key)
    
    def update_context(self, session_id: str, context: Dict[str, Any]) -> None:
        """Update session context."""
        context_key = f"context:{session_id}"
        self.redis_client.setex(
            context_key,
            self.history_ttl,
            json.dumps(context)
        )
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context."""
        context_key = f"context:{session_id}"
        context_data = self.redis_client.get(context_key)
        if context_data:
            return json.loads(context_data)
        return {} 