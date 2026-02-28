import os
import shutil
import asyncio
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 12 hours in seconds
CLEANUP_INTERVAL_SECONDS = 12 * 60 * 60

class StorageCleanupManager:
    """
    Manages periodic cleanup of the storage directory except for the logs.
    """
    def __init__(self):
        # Resolve storage directory relative to the project root (assuming this file is in src/utils/)
        self._project_root = Path(__file__).resolve().parents[2]
        self._storage_dir = self._project_root / "storage"

    def start_cleanup(self):
        """Starts the background cleanup task. Must be called within a running event loop."""
        asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Periodically removes all contents in the storage directory except 'logs'."""
        while True:
            # We can run the cleanup immediately on startup, or wait.
            # Running immediately helps clean up any stale files from a previous crashed run.
            try:
                self._perform_cleanup()
            except Exception as e:
                logger.error(f"StorageCleanupManager: Cleanup failed: {e}")
                
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)

    def _perform_cleanup(self):
        if not self._storage_dir.exists():
            return
            
        logger.info(f"StorageCleanupManager: Starting cleanup of {self._storage_dir} (excluding 'logs')")
        deleted_count = 0
        
        for item in self._storage_dir.iterdir():
            if item.name == "logs":
                continue # Skip the logs directory
                
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                deleted_count += 1
                logger.debug(f"StorageCleanupManager: Deleted {item.name}")
            except Exception as e:
                logger.warning(f"StorageCleanupManager: Failed to delete {item.name}: {e}")
                
        if deleted_count > 0:
            logger.info(f"StorageCleanupManager: Cleanup finished. Deleted {deleted_count} items.")
        else:
            logger.debug("StorageCleanupManager: Cleanup finished. No items to delete.")

        # Also clear generic anonymous sessions that leaked because session wasn't closed by the user
        from src.utils.memory_manager import memory_manager
        memory_manager.clear_stale_anonymous_sessions()

# Global instance
storage_cleanup_manager = StorageCleanupManager()
