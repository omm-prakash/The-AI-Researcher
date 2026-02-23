import os
from contextlib import contextmanager
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/langgraph_db")

# Initialize a global connection pool once to handle highly concurrent API requests safely
pool = ConnectionPool(conninfo=DATABASE_URL, max_size=20, kwargs={"autocommit": True})

def setup_database():
    """Ensure the database tables are created. Call this once on startup."""
    checkpointer = PostgresSaver(pool)
    store = PostgresStore(pool)
    checkpointer.setup()
    store.setup()

setup_database()

@contextmanager
def get_postgres_setup():
    """
    Yields a (checkpointer, store) tuple from the global concurrent connection pool.
    """
    checkpointer = PostgresSaver(pool)
    store = PostgresStore(pool)
    yield checkpointer, store
