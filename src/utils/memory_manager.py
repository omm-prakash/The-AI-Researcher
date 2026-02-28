import os
import time
import asyncio
from typing import List, Dict
from supabase import create_client, Client
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from src.utils.logger import get_logger

logger = get_logger(__name__)

class SessionMemoryManager:
    """
    Manages in-memory caching of chat history, backed by Supabase.
    Fetches chat history from Supabase only once per session.
    Automatically evicts inactive sessions to save memory.
    """
    
    def __init__(self, ttl_seconds: int = 1800):
        url: str = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
        key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.warning("Supabase URL or Key not found in environment variables.")
            self.supabase: Client | None = None
        else:
            self.supabase: Client = create_client(url, key)
            
        # Cache format: { "thread_id": {"messages": [...], "last_accessed": float} }
        self.cache: Dict[str, Dict] = {}
        self.ttl_seconds = ttl_seconds

    def start_cleanup(self):
        """Starts the background cleanup task. Must be called within a running event loop."""
        asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Periodically remove inactive sessions from RAM."""
        while True:
            await asyncio.sleep(300) # Check every 5 minutes
            now = time.time()
            stale_threads = [
                tid for tid, data in self.cache.items()
                if (now - data["last_accessed"] > self.ttl_seconds) and (data.get("user_id") != "anonymous")
            ]
            for tid in stale_threads:
                del self.cache[tid]
            if stale_threads:
                logger.info(f"MemoryManager: Cleared {len(stale_threads)} stale sessions.")

    def get_or_load_session(self, thread_id: str, user_id: str) -> List[BaseMessage]:
        """
        Retrieves the message history from cache, or loads it from Supabase if not cached.
        """
        now = time.time()
        
        if thread_id in self.cache:
            logger.debug(f"MemoryManager: Cache hit for thread {thread_id}")
            self.cache[thread_id]["last_accessed"] = now
            return list(self.cache[thread_id]["messages"])

        logger.info(f"MemoryManager: Cache miss for thread {thread_id}. Fetching from Supabase.")
        messages = []
        
        if self.supabase and user_id != 'anonymous':
            try:
                # Query history, ordered by creation time
                response = self.supabase.table("chat_history") \
                    .select("role, content") \
                    .eq("conversation_id", thread_id) \
                    .eq("user_id", user_id) \
                    .order("created_at") \
                    .execute()
                    
                for row in response.data:
                    if row["role"] == "user":
                        messages.append(HumanMessage(content=row["content"]))
                    elif row["role"] == "assistant":
                        messages.append(AIMessage(content=row["content"]))
                        
            except Exception as e:
                logger.error(f"MemoryManager: Failed to fetch from Supabase: {e}")
        
        self.cache[thread_id] = {
            "messages": messages,
            "last_accessed": now,
            "user_id": user_id
        }
        return list(messages)

    def update_session(self, thread_id: str, new_messages: List[BaseMessage]):
        """
        Appends new messages to the existing cached session.
        """
        if thread_id in self.cache:
            self.cache[thread_id]["messages"].extend(new_messages)
            self.cache[thread_id]["last_accessed"] = time.time()
            
    def delete_session(self, thread_id: str):
        """
        Deletes a session from the cache.
        """
        if thread_id in self.cache:
            del self.cache[thread_id]
            logger.info(f"MemoryManager: Deleted session {thread_id} from cache.")

    def clear_stale_anonymous_sessions(self, max_age_seconds: int = 43200):
        """
        Clears anonymous sessions older than max_age_seconds (default 12 hours) to avoid memory leaks.
        """
        now = time.time()
        stale = [
            tid for tid, data in self.cache.items()
            if data.get("user_id") == "anonymous" and (now - data["last_accessed"] > max_age_seconds)
        ]
        for tid in stale:
            del self.cache[tid]
        if stale:
            logger.info(f"MemoryManager: Cleared {len(stale)} stale anonymous sessions.")

# Global instance
memory_manager = SessionMemoryManager()
