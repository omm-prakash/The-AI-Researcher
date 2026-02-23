import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from src.graph.builder import build_graph
from src.database import get_postgres_setup
from src.middlewares import setup_middlewares
from langchain_core.messages import HumanMessage

from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for the local Vite frontend
CORS(app, resources={r"/*": {"origins": "*"}})

# Add Middlewares
setup_middlewares(app)

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """
    Endpoint to interact with the multi-agent system.
    Persists chats to a PostgreSQL database via langgraph-checkpoint-postgres and langgraph.store.postgres.
    """
    try:
        data = request.get_json()
        if not data or "thread_id" not in data or "message" not in data:
            return jsonify({"error": "Missing thread_id or message in request body"}), 400

        thread_id = data["thread_id"]
        message_text = data["message"]
        
        builder = build_graph()
        
        with get_postgres_setup() as (checkpointer, store):
            # Compile the graph with Checkpointer and Store
            graph = builder.compile(checkpointer=checkpointer, store=store)
            
            config = {"configurable": {"thread_id": thread_id}}
            
            # Start execution graph
            input_message = HumanMessage(content=message_text)
            
            # Use sync invoke as the checkpointer is synchronous
            final_state = graph.invoke(
                {"messages": [input_message]},
                config=config
            )
            
            if final_state and "messages" in final_state and len(final_state["messages"]) > 0:
                final_response = final_state["messages"][-1].content
            else:
                final_response = "No response generated."
                
            return jsonify({"response": final_response, "thread_id": thread_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
