from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.graph.builder import build_graph
from src.database import get_checkpointer
from src.middlewares import AgenticMiddleware
import asyncio
from langchain_core.messages import HumanMessage

app = FastAPI(title="Agentic Research Assistant API")

# Add Middlewares
app.add_middleware(AgenticMiddleware)

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    thread_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint to interact with the multi-agent system.
    Persists chats to PostgreSQL via langgraph-checkpoint-postgres.
    """
    try:
        builder = build_graph()
        
        async with get_checkpointer() as checkpointer:
            # Compile the graph with the Checkpointer
            graph = builder.compile(checkpointer=checkpointer)
            
            config = {"configurable": {"thread_id": request.thread_id}}
            
            # Start execution graph
            input_message = HumanMessage(content=request.message)
            
            # Streaming or invoking the graph
            final_state = await graph.ainvoke(
                {"messages": [input_message]},
                config=config
            )
            
            if final_state and "messages" in final_state and len(final_state["messages"]) > 0:
                final_response = final_state["messages"][-1].content
            else:
                final_response = "No response generated."
                
            return ChatResponse(response=final_response, thread_id=request.thread_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
