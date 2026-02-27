import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables before setting up logging or importing dependents
load_dotenv()

from src.utils.logger import setup_logging, get_logger
setup_logging()   # must be first — before any other src imports

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List

from src.graph.builder import build_graph
from src.utils.memory_manager import memory_manager
from src.middlewares import LoggingMiddleware
from langchain_core.messages import HumanMessage, AIMessage
from contextlib import asynccontextmanager

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the memory manager's cache eviction loop on boot
    memory_manager.start_cleanup()
    yield

app = FastAPI(title="TAR: The AI Researcher API", version="1.0.0", lifespan=lifespan)

# Enable CORS for the local Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing/logging middleware
app.add_middleware(LoggingMiddleware)

# Build graph once at startup — avoid rebuilding on every request
_graph_builder = build_graph()


# ── Request model for JSON-based requests ────────────────────────────────────
class ChatRequest(BaseModel):
    thread_id: str
    message: str


# ── Helper: infer attachment type from file extension ────────────────────────
def _get_attachment_type(filename: str) -> str:
    ext = filename.lower().rsplit('.', 1)[-1]
    if ext == 'pdf':
        return 'pdf'
    elif ext in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
        return 'image'
    elif ext in ('mp3', 'wav', 'ogg', 'm4a'):
        return 'audio'
    return 'none'


# ── Main chat endpoint ────────────────────────────────────────────────────────
@app.post("/chat")
async def chat_endpoint(request: Request):
    """
    Chat endpoint that handles both JSON and multipart/form-data.
    Uses Supabase and local TTL cache for memory instead of Postgres checkpointer.
    """
    thread_id = None
    user_id = None
    message = None
    attachment_type = "none"
    attachment_path = None

    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        # ── JSON body (no files) ──────────────────────────────────────────
        body = await request.json()
        thread_id = body.get("thread_id")
        user_id = body.get("user_id")
        message = body.get("message")
    else:
        # ── Multipart form-data (with or without files) ───────────────────
        form = await request.form()
        thread_id = form.get("thread_id")
        user_id = form.get("user_id")
        message = form.get("message")
        files = form.getlist("files")

        if files:
            latest_file = files[-1]
            if hasattr(latest_file, "filename") and latest_file.filename:
                storage_dir = os.path.join("storage", thread_id)
                os.makedirs(storage_dir, exist_ok=True)

                safe_name = os.path.basename(latest_file.filename)
                file_path = os.path.join(storage_dir, safe_name)

                content = await latest_file.read()
                with open(file_path, "wb") as f:
                    f.write(content)

                attachment_path = file_path
                attachment_type = _get_attachment_type(safe_name)

    if not thread_id or not message or not user_id:
        raise HTTPException(status_code=400, detail="Missing thread_id, user_id, or message in request body")

    logger.debug("/chat payload: thread_id=%s user_id=%s message=%s", thread_id, user_id, message[:80])

    # ── Load history from Memory Manager (Supabase backed) ─────────────────
    history = memory_manager.get_or_load_session(thread_id, user_id)
    input_message = HumanMessage(content=message)
    
    # LangGraph expects the full list of messages when running statelessly.
    current_messages = history + [input_message]

    # ── Invoke the LangGraph agent ────────────────────────────────────────
    # Compile statelessly without a checkpointer
    graph = _graph_builder.compile()
    
    config = {"configurable": {"thread_id": thread_id}}
    logger.info("/chat thread=%s  attachment_type=%s", thread_id, attachment_type)

    final_state = graph.invoke(
        {
            "messages": current_messages,
            "attachment_type": attachment_type,
            "attachment_path": attachment_path,
            "error_response": "",   # reset stale error from previous run on this thread
        },
        config=config
    )

    if final_state and 'error_response' in final_state and final_state["error_response"]:
        final_response = final_state["error_response"]
        logger.warning("/chat returning error_response for thread=%s", thread_id)
    elif final_state and "messages" in final_state and len(final_state["messages"]) > 0:
        final_response = final_state["messages"][-1].content
        logger.info("/chat response ready for thread=%s (%d chars)", thread_id, len(final_response))
        
        # ── Save current interaction to local memory cache ────────────────
        ai_message = AIMessage(content=final_response)
        memory_manager.update_session(thread_id, [input_message, ai_message])
        
    else:
        final_response = "No response generated."
        logger.warning("/chat no response generated for thread=%s", thread_id)

    return JSONResponse(content={"response": final_response, "thread_id": thread_id})


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", 
                host="0.0.0.0", 
                port=8000, 
                reload=True, 
                reload_excludes=['storage/*', 'venv', '.env', '__pycache__', '.git', '.idea', '.vscode']
                )
