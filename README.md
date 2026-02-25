# 🤖 Agentic Research Assistant

A production-ready, **multi-agent AI research assistant** built with **LangGraph** and **Flask**. Given any query, it autonomously gathers information from the web, processes attachments (PDFs, images, audio), synthesizes findings, and drafts a comprehensive report — all persisted natively in **PostgreSQL**.

> Designed as an end-to-end reference implementation showcasing modern agentic AI patterns: context engineering, multi-agent orchestration, stateful memory, guardrails, and multimodal file handling.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **Multi-Agent Orchestration** | Supervisor routes tasks to specialized Researcher, Writer, and Casual subagents via LangGraph |
| 🛡️ **Guardrail Node** | Content moderation filter runs before any agent execution |
| 🔍 **Web Search** | Researcher agent performs live DuckDuckGo / Tavily internet searches |
| 📎 **Multimodal Attachments** | Supports PDF, image (JPG/PNG/WebP), and audio (MP3/WAV/M4A) file uploads |
| 🗄️ **Persistent Memory** | Native PostgreSQL checkpointing stores full conversation thread history |
| 💬 **Session Management** | Per-thread conversation state using `thread_id` |
| 🌐 **Vue 3 Frontend** | Lightweight chat interface built with Vue 3 + Vite |
| ⚡ **Context Engineering** | Dynamic chunking prevents LLM context-window overflow |
| 🔧 **Flask Middlewares** | Request logging, latency tracking, and extensible moderation hooks |

---

## 🏗️ Architecture

```
User Request
     │
     ▼
┌──────────┐
│ Guardrail│  ← Content moderation
└──────────┘
     │
     ▼
┌────────────┐
│ Supervisor │  ← Routing decision
└────────────┘
     │
     ├──────────────────┐
     ▼                  ▼
┌────────────┐    ┌────────┐
│ Researcher │    │ Casual │
└────────────┘    └────────┘
     │
     ├── [Tool Call?] ──► ┌───────┐
     │                    │ Tools │ ← Web search, PDF, Image, Audio
     │                    └───────┘
     │                        │
     │ ◄──────────────────────┘
     ▼
┌────────┐
│ Writer │  ← Synthesizes final report
└────────┘
     │
     ▼
 Response
```

### Agent Roles

- **Guardrail** — First-pass content filter; blocks harmful or off-topic inputs before they reach any agent.
- **Supervisor** — Decides whether to route to `Researcher` (complex queries), `Casual` (simple chat), or terminate.
- **Researcher** — Queries the web and processes any uploaded files using tool calls.
- **Writer** — Reads the researcher's gathered facts and synthesizes a polished, structured report.
- **Casual** — Handles conversational messages that don't require research.

---

## 📁 Project Structure

```
agent-project/
├── src/
│   ├── main.py               # Flask app entry point & /chat endpoint
│   ├── database.py           # PostgreSQL checkpointer & store setup
│   ├── middlewares.py        # Request logging & latency middleware
│   ├── graph/
│   │   ├── builder.py        # LangGraph StateGraph construction
│   │   ├── state.py          # AgentState TypedDict definition
│   │   ├── llms.py           # LLM model configurations (Groq)
│   │   ├── prompts.py        # Role-based system prompts
│   │   └── nodes/
│   │       ├── supervisor.py # Routing supervisor node
│   │       ├── researcher.py # Web search & file analysis node
│   │       ├── writer.py     # Report synthesis node
│   │       ├── casual.py     # Conversational node
│   │       └── guardrail.py  # Content moderation node
│   ├── tools/
│   │   ├── search.py         # DuckDuckGo / Tavily internet search tool
│   │   ├── read_pdf.py       # PDF extraction tool (LLM-assisted)
│   │   ├── read_image.py     # Image understanding tool (vision LLM)
│   │   └── read_audio.py     # Audio transcription & summarization tool
│   └── utils/
│       └── context.py        # Context chunking & management utilities
├── frontend/                 # Vue 3 + Vite chat UI
│   ├── src/
│   │   ├── App.vue
│   │   ├── components/
│   │   └── style.css
│   └── package.json
├── storage/                  # Uploaded files (per thread_id)
├── tests/                    # Pytest test suite
├── langgraph.json            # LangGraph deployment config
├── requirements.txt
└── .env                      # Environment variables (not committed)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+, Flask, Flask-CORS |
| **AI Framework** | LangChain, LangGraph |
| **LLM Provider** | Groq (`llama3-8b-8192`, `llama3-70b-8192`) |
| **Web Search** | DuckDuckGo Search, Tavily |
| **State Persistence** | PostgreSQL via `langgraph-checkpoint-postgres` + `psycopg` |
| **Frontend** | Vue 3, Vite, Marked.js |
| **Deployment** | Hypercorn (ASGI), LangGraph Cloud compatible |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- A running **PostgreSQL** instance
- A [Groq API key](https://console.groq.com/)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/agent-project.git
cd agent-project
```

### 2. Set up the Python environment

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
# LLM
GROQ_API_KEY=your_groq_api_key

# PostgreSQL (for state persistence)
DB_URI=postgresql://user:password@localhost:5432/agent_db

# Optional: Tavily (alternative web search)
TAVILY_API_KEY=your_tavily_api_key
```

### 4. Start the Flask backend

```bash
python src/main.py
```

The API will be available at `http://localhost:8000`.

### 5. Start the Vue frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

The chat UI will be available at `http://localhost:5173`.

---

## 🔌 API Reference

### `POST /chat`

Interact with the multi-agent system. Supports both JSON and multipart form data (for file uploads).

**JSON Request:**

```http
POST http://localhost:8000/chat
Content-Type: application/json

{
  "thread_id": "session_001",
  "message": "What are the latest advancements in solid-state batteries?"
}
```

**Multipart Request (with file attachment):**

```
POST http://localhost:8000/chat
Content-Type: multipart/form-data

thread_id=session_001
message=Summarize this document
files=@/path/to/document.pdf
```

**Response:**

```json
{
  "response": "## Solid-State Batteries: 2024 Advancements\n\n...",
  "thread_id": "session_001"
}
```

### Supported Attachment Types

| Extension | Type | Handling |
|---|---|---|
| `.pdf` | PDF | LLM-assisted text extraction |
| `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` | Image | Vision LLM analysis |
| `.mp3`, `.wav`, `.ogg`, `.m4a` | Audio | Transcription & summarization |

---

## 🧪 Running Tests

```bash
pytest tests/
```

---

## 🗺️ Roadmap

- [ ] Streaming responses via Server-Sent Events (SSE)
- [ ] LangGraph Studio deployment support
- [ ] Additional tool integrations (e.g., code execution, Wikipedia)
- [ ] User authentication and multi-user session management
- [ ] Docker Compose setup for one-command deployment

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
