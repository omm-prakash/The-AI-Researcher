# Agentic Research Assistant

This project is an end-to-end multi-agent workflow solution, showcasing modern **Agent Development** architectures using **LangGraph** and **Flask**. It functions as an autonomous research assistant that takes a query, gathers facts via web search, synthesizes information, and drafts a robust report.

## 🚀 Key Features Demonstrated

- **Context Engineering**: Dynamically retrieves, chunks, and manages context to prevent LLM context-window overflow (`src/utils/context.py`).
- **Prompt Engineering**: Role-based prompts (Supervisor, Researcher, Writer) ensuring reliable routing and responses (`src/graph/prompts.py`).
- **Proper Middlewares**: Flask request middleware implementation for logging, latency tracking, and extensible moderation (`src/middlewares.py`).
- **Subagents (Multi-Agent System)**: A dynamic LangGraph system utilizing a **Supervisor Node** to route tasks to independent **Researcher** and **Writer** nodes (`src/graph/`).
- **Native Postgres for State Persistence**: Uses `langgraph.store.postgres` (`PostgresStore`) to store generalized agent state and `langgraph-checkpoint-postgres` to store conversational thread histories natively (`src/database.py`).

## 🛠️ Stack & Technologies Used

- **Python / Flask**: Backend REST framework.
- **LangChain / LangGraph**: Core orchestration and agent framework.
- **Groq AI Framework**: Native integration utilizing fast `llama3-8b-8192` and `llama3-70b-8192` endpoints natively via `langchain-groq`.
- **DuckDuckGo Search**: Web search subagent custom tool.
- **PostgreSQL Database**: Purely native stateful agent memory checkpointer featuring `psycopg[binary]`.

## ⚙️ Getting Started

1. **Install dependencies:**

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment variables:**
   Copy `.env.example` to `.env` and fill in your API keys:

   ```bash
   cp .env.example .env
   ```

3. **Run the API:**

   ```bash
   python src/main.py
   ```

4. **Interact:**
   Send a chat payload to the endpoint via a tool like curl or Postman:

   ```json
   POST http://localhost:8000/chat
   {
       "thread_id": "session_001",
       "message": "What are the latest advancements in solid-state batteries?"
   }
   ```
