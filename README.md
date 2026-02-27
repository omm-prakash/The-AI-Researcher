# TAR: The AI Researcher

> **High-Level Value Prop**: TAR (The AI Researcher) is an advanced, multi-agent AI system designed to conduct deep, autonomous internet research and process multi-modal attachments (PDFs, Images, Audio). By leveraging a robust, event-driven graph architecture, TAR provides highly accurate, context-aware, and thoroughly researched responses, minimizing hallucinations and maximizing depth.

<p align="center"><img src="ref-images/frontend.png" width="800"></p>

---

## 🏗️ System Architecture

TAR employs a **modular frontend-backend separation** to ensure scalability, maintainability, and clear boundaries of concern.

- **Frontend**: A highly responsive, single-page application built with **Vue 3** and **Vite**. It provides a real-time conversational interface designed for low-latency streaming and seamless multi-modal file uploads. It utilizes **Supabase** for user authentication and session management, and **KaTeX** for rendering LaTeX mathematical equations.
- **Backend / Engine**: A **FastAPI-based API** acting as the gateway to our core reasoning engine. The engine itself is an **event-driven state machine** orchestrated via **LangGraph**, served efficiently via **Uvicorn**.
- **State & Persistence**: Long-term conversational memory, user profiles, and chat history are persisted to **Supabase** (PostgreSQL under the hood). Short-term state is managed in-memory as the graph executes, with a local TTL cache manager optimizing memory usage and minimizing database roundtrips.

---

## 🧠 Agentic Workflow & Reasoning

The core intelligence of TAR relies on a sophisticated Multi-Agent architecture. Unlike linear chains, TAR functions as an autonomous research team, exhibiting continuous evaluation, tool use, and reflection.

<p align="center">
<img src="ref-images/workflow.png" >
</p>

### 1. Planning & Routing (The Supervisor)

- When a request enters the system, it is first evaluated by a **Guardrail** node for safety.
- If approved, the **Supervisor Agent** (powered by Logic/Reasoning LLMs) takes over. The Supervisor analyzes the intent and dynamically determines the optimal execution path.
- If the request involves casual conversation, it routes to a **Casual Agent**.
- If it requires deep research, it invokes the **Researcher Agent**.

**Multi-modal Interception:** Crucially, if the payload contains attachments (PDF, Image, Audio), the system circumvents text-only routing and immediately assigns the request to a **Specialist Subagent** (PDFAgent, ImageAgent, or AudioAgent) to preemptively extract context before research begins. Document parsing and multi-modal handling are dynamically addressed by the graph processing.

### 2. Tool Usage (The Researcher)

The **Researcher Agent** is the workhorse of the graph. It is bound to multiple tools:

- **Web Search**: Primary tool for AI-optimized, deterministic internet searches.
- **Web Extract**: Used selectively to scrape and parse full raw content from targeted, high-value URLs.
- *Fallback Mechanism*: If Tavily fails or hits rate limits, the agent autonomously falls back to a **DuckDuckGo** search integration to ensure fault tolerance.

### 3. Reflection & Looping

TAR's execution is cyclical rather than linear. The Researcher Agent evaluates the results from its tool calls. If the scraped data is insufficient, it formulates new queries and loops back to the search tools. Once it confidently holds the required knowledge, the internal state shifts and hands off to the **Writer Agent**, which synthesizes the raw data into a polished, definitive answer.

### 4. Memory Management

Context is securely maintained across turns using **Supabase** for persistent chat history. The FastAPI backend employs a **SessionMemoryManager** that caches conversations locally with a TTL mechanism, periodically evicting stale sessions while constantly syncing with Supabase for long-term storage.

---

## 🛠️ Tech Stack

| Technology | Purpose | Selection Rationale |
| :--- | :--- | :--- |
| **LangGraph** | Orchestration & Workflow | Chosen for its cyclic state-machine capabilities, enabling true multi-agent looping and reflection. |
| **LangChain** | LLM Abstraction | Selected for standardized tool-binding and dynamic model fallback integrations. |
| **FastAPI + Uvicorn** | Backend API | Chosen for rapid prototyping, incredible asynchronous performance, and lightweight deployment. |
| **Supabase** | Memory, State, & Auth | Selected for highly concurrent, serverless-friendly PostgreSQL guarantees, handling both auth and conversational history seamlessly. |
| **Vue 3 + Vite** | Frontend Interface | Chosen for its reactive virtual DOM footprint, enabling fast-loading, highly interactive user experiences with KaTeX rendering. |
| **Tavily API** | Search Infrastructure | Selected over standard SERP APIs for its ability to return LLM-optimized search context and raw HTML extraction. |

---

## 🤖 Default LLMs and Model Routing

TAR is fundamentally model-agnostic but is configured by default to utilize a Mixture of Experts (MoE) approach via Groq and Google GenAI. Models are categorized by their specific strengths:

- **Logic & Reasoning** (e.g., `qwen3-32b`, `llama-3.3-70b`): Used by the **Supervisor Agent** to break down tasks and make routing decisions, and acts as a fallback for analyzing complex PDF chunks.
- **Agentic Systems** (e.g., `gpt-oss-20b`, `kimi-k2-instruct`): Leveraged by the **Researcher Agent** for their superior tool-calling and function-binding capabilities.
- **Multi-Modal Understanding** (`gemini-2.5-flash-lite`): Powered by Google GenAI. Selected for its rapid processing speed and massive 20k+ token context window, enabling entire document ingestion in one pass (PDF, Audio, Image).
- **Safety & Security** (e.g., `llama-prompt-guard-2`, `gpt-oss-safeguard`): Utilized strictly by the Guardrail edge node to classify prompts and prevent prompt injection or policy violations.

---

## 🚀 Key Features

- **Multi-Agent Orchestration**: Specialized agents (Supervisor, Researcher, Writer) handling discrete tasks for massively improved processing and output quality.
- **Multi-Modal Document Ingestion**: Intelligent, format-specific subagents capable of parsing PDFs, Images, and Audio files via multimodal AI integrations.
- **Self-Healing Tool Execution**: Automatic failover from Tavily Search to DuckDuckGo if primary endpoints fail, ensuring 100% uptime on research paths.
- **Persistent Conversational Memory**: Thread-based state management leveraging Supabase and local TTL cache allows users to resume deep-dive research sessions across multiple days seamlessly.
- **Scientific Equation Display**: Native LaTeX rendering in the frontend chat interface to display complex mathematical and scientific contexts.

---

## 💻 Getting Started

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/omm-prakash/The-AI-Researcher.git
cd The-AI-Researcher

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Configure Environment Variables
cp .env.example .env
# Important: Fill in your GROQ_API_KEY, TAVILY_API_KEY, GOOGLE_API_KEY, 
# SUPABASE_URL, and SUPABASE_SERVICE_ROLE_KEY inside .env

# Run the FastAPI server in Development
python src/main.py
```

### 2. Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Setup Frontend Environment Variables
# Create a .env file and add your VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY

# Start the Vite development server
npm run dev
```

### 3. Production Deployment

TAR includes basic scripts for deploying the application on a Linux-based Virtual Machine (like AWS EC2, GCP Compute, or OCI Instances) running `pm2`.

```bash
# Run the deployment helper (which pulls branch updates, installs deps, and starts pm2 with uvicorn configurations)
./deploy.sh
```

---

## 🗺️ Future Roadmap

- **Vector Database Integration (RAG)**: Implementing Pinecone to provide persistent, long-term memory mapping of past research sessions, turning TAR into a personalized second brain.
- **Dockerization & Kubernetes**: Dockerizing the application and writing Helm charts to scale the processing worker nodes in a Kubernetes cluster horizontally.
- **Advanced User Authentication**: Integrating more robust enterprise single-sign on (SSO) and granular role-based access.

*I am actively working on the project, and will change the README.md file as the project progresses.*
