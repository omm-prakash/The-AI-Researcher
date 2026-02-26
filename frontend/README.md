# TAR Frontend: The AI Researcher User Interface

This is the frontend component of **TAR (The AI Researcher)**. It is a highly responsive, single-page application (SPA) designed to provide a real-time, interactive chat interface for multi-modal AI research.

## ⚡ Tech Stack

| Technology | Purpose |
| :--- | :--- |
| **Vue 3** (Composition API) | Core UI framework for building reactive and performant components. |
| **Vite** | Next-generation frontend tooling and fast-bundler for instantaneous HMR (Hot Module Replacement). |
| **Marked** | Used for rapidly parsing and rendering markdown responses from the AI agents. |
| **KaTeX** | Integrated for high-quality mathematical typesetting and formula rendering within AI responses. |

## ✨ Key Features

- **Real-Time Responsiveness**: Optimized for low-latency interactions to provide a snappy chatting experience.
- **Multi-Modal Capabilities**: Supports dragging, dropping, and pasting of images, PDFs, and audio files directly into the chat interface for processing by specialized subagents.
- **Rich Text Rendering**: Full markdown parsing, code syntax highlighting, and KaTeX mathematical formula rendering.
- **Stateless/Stateful Context**: Readily interfaces with the `thread_id` system to allow resumable conversational state mapped to the PostgreSQL backend context.

## 🛠️ Getting Started

### Prerequisites

Ensure you have [Node.js](https://nodejs.org/) (version 18+ recommended) and `npm` installed.

### Installation

1. Navigate to the `frontend` directory (if you aren't already there):

   ```bash
   cd frontend
   ```

2. Install the necessary dependencies:

   ```bash
   npm install
   ```

### Development Server

To spin up the development server with Hot Module Replacement (HMR):

```bash
npm run dev
```

*The application will typically be accessible at `http://localhost:5173/` by default.*

### Building for Production

When you're ready to deploy the frontend to a production environment:

```bash
# Creates an optimized production build in the `dist/` directory
npm run build

# To locally preview the production build
npm run preview
```

## 🔌 API Integration

The frontend expects the TAR Flask backend to be running locally on port `8000` (e.g., `http://127.0.0.1:8000`). Make sure your backend API is accessible so that cross-origin requests (CORS) succeed when the UI makes queries to the `/chat` endpoint.
