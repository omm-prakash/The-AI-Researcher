# Agentic Research Assistant

This project is an end-to-end multi-agent workflow solution, showcasing modern **Agent Development** architectures using **LangGraph** and **FastAPI**. It functions as an autonomous research assistant that takes a query, gathers facts via web search, synthesizes information, and drafts a robust report.

## 🚀 Key Features Demonstrated

- **Context Engineering**: Dynamically retrieves, chunks, and manages context to prevent LLM context-window overflow (`src/utils/context.py`).
- **Prompt Engineering**: Role-based prompts (Supervisor, Researcher, Writer) ensuring reliable routing and responses (`src/graph/prompts.py`).
- **Proper Middlewares**: FastAPI middleware implementation for logging, latency tracking, and extensible moderation (`src/middlewares.py`).
- **Subagents (Multi-Agent System)**: A dynamic LangGraph system utilizing a **Supervisor Node** to route tasks to independent **Researcher** and **Writer** nodes (`src/graph/`).
- **Postgres for State Persistence**: Uses `langgraph-checkpoint-postgres` to store chat histories allowing state resilience and session resuming (`src/database.py`).

## 🛠️ Stack & Technologies Used
- **Python / FastAPI**: Backend REST framework.
- **LangChain / LangGraph**: Core orchestration and agent framework.
- **Groq & OpenAI Oss Layer**: Uses fast LLaMA/Mixtral LLM models hosted via Groq via `langchain-groq`.
- **Tavily**: Web search subagent tool integration.
- **PostgreSQL**: Stateful agent memory checkpointer.
- **Docker**: Containerized database management.

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

3. **Start PostgreSQL Database:**
   Ensure Docker is installed, then spin up the checkpointer DB:
   ```bash
   docker compose up -d
   ```

4. **Run the API:**
   ```bash
   uvicorn src.main:app --reload
   ```

5. **Interact:**
   Send a chat payload to the endpoint via a tool like curl or Postman:
   ```json
   POST http://localhost:8000/chat
   {
       "thread_id": "session_001",
       "message": "What are the latest advancements in solid-state batteries?"
   }
   ```
