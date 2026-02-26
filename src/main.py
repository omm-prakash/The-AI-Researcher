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

# Build graph once at startup — avoid rebuilding on every request
_graph_builder = build_graph()

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """
    Endpoint to interact with the multi-agent system.
    Persists chats to a PostgreSQL database via langgraph-checkpoint-postgres and langgraph.store.postgres.
    """    
    # Handle both Application/JSON and Multipart/Form-Data
    # print('\n\nrequest', request)
    if request.is_json:
        data = request.get_json()
        print(data)
        thread_id = data.get("thread_id")
        message_text = data.get("message")
        files = []
    else:
        thread_id = request.form.get("thread_id")
        message_text = request.form.get("message")
        files = request.files.getlist("files")
        
    if not thread_id or not message_text:
        return jsonify({"error": "Missing thread_id or message in request body"}), 400

    from werkzeug.utils import secure_filename
    
    attachment_type = "none"
    attachment_path = None
    
    if files:
        latest_file = files[-1]
        if latest_file.filename:
            # Create session storage directory
            storage_dir = os.path.join("storage", thread_id)
            os.makedirs(storage_dir, exist_ok=True)
            
            filename = secure_filename(latest_file.filename)
            file_path = os.path.join(storage_dir, filename)
            latest_file.save(file_path)
            
            attachment_path = file_path
            ext = filename.lower().split('.')[-1]
            if ext == 'pdf':
                attachment_type = "pdf"
            elif ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                attachment_type = "image"
            elif ext in ['mp3', 'wav', 'ogg', 'm4a']:
                attachment_type = "audio"
    
    builder = _graph_builder
    
    with get_postgres_setup() as (checkpointer, store):
        # Compile the graph with Checkpointer and Store
        graph = builder.compile(checkpointer=checkpointer, store=store)
        
        config = {"configurable": {"thread_id": thread_id}}
        print()
        print(config, message_text)
        print()
        # Start execution graph
        input_message = HumanMessage(content=message_text)
        
        final_state = graph.invoke(
            {
                "messages": [input_message],
                "attachment_type": attachment_type,
                "attachment_path": attachment_path,
                "error_response": "",   # reset stale error from previous run on this thread
            },
            config=config
        )
        
        if final_state and 'error_response' in final_state and final_state["error_response"]:
            final_response = final_state["error_response"]
        elif final_state and "messages" in final_state and len(final_state["messages"]) > 0:
            final_response = final_state["messages"][-1].content
        else:
            final_response = "No response generated."

        # NOTE: attachment_type is passed fresh every request from the frontend,
        # so there is no need to write it back to the checkpoint here.
        return jsonify({"response": final_response, "thread_id": thread_id})

    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)



