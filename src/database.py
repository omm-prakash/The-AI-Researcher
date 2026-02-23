import os
import asyncpg
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from contextlib import asynccontextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/langgraph_db")

@asynccontextmanager
async def get_checkpointer():
    """
    Yields an AsyncPostgresSaver initialized with the connection pool.
    Usage:
    async with get_checkpointer() as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)
        # Use graph
    """
    # Create the asyncpg connection pool
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        # Initialize the checkpointer
        checkpointer = AsyncPostgresSaver(pool)
        
        # Ensure the schema is created (typically needed once)
        await checkpointer.setup()
        
        yield checkpointer
