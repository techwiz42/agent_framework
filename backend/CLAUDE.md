# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

The project consists of two main parts: a Python FastAPI backend and a TypeScript/Next.js frontend.

## Development Environment

### Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings (API keys, database config, etc.)

# Run database migrations
alembic upgrade head
```

### Running the Backend
```bash
# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing the Backend
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api/test_auth.py

# Run tests with coverage
pytest --cov=app tests/
```

### Frontend Setup
```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your settings
```

### Running the Frontend
```bash
# Start development server
npm run dev
```

### Frontend Commands
```bash
# Run linting
npm run lint

# Build for production
npm run build

# Run production build
npm run start
```

## Architecture Overview

### Agent System

The Agent Framework is structured around a modular, extensible agent-based architecture:

1. **BaseAgent** (`app/services/agents/base_agent.py`): Abstract base class that wraps around LLM APIs, provides tool registration, context management, and execution handling.

2. **AgentInterface** (`app/services/agents/agent_interface.py`): Central registry for managing agents, handles agent instantiation, registration, and retrieval.

3. **ModeratorAgent** (`app/services/agents/moderator_agent.py`): Special agent that routes user queries to appropriate specialist agents based on content analysis.

4. **CollaborationManager** (`app/services/agents/collaboration_manager.py`): Orchestrates multi-agent collaborations, distributes tasks, and synthesizes responses.

5. **Specialized Agents**: Domain-specific agents (business, web search, data analysis, etc.) that inherit from BaseAgent and implement specialized tools and knowledge.

### Real-Time Communication

The application uses WebSockets for real-time communication:

1. **WebSocket Endpoints** (`app/api/websockets.py`): Handles client connections, message processing, and agent routing.

2. **WebSocketQueue** (`app/core/websocket_queue.py`): Manages connection health, message queuing, and delivery guarantees.

3. **ProgressManager** (`app/core/progress_manager.py`): Provides progress updates for long-running operations.

4. **ConversationAPI** (`app/api/conversations.py`): Manages conversation lifecycle and persistence.

### Creating a New Agent

To add a new specialized agent:

1. Create a new file in `app/services/agents/` (e.g., `custom_agent.py`)
2. Inherit from BaseAgent and implement specific tools and instructions
3. Register the agent in `app/services/agents/__init__.py`

Example pattern:
```python
from app.services.agents.base_agent import BaseAgent, AgentHooks

class CustomAgent(BaseAgent):
    def __init__(self, name="CUSTOM"):
        super().__init__(
            name=name,
            model=settings.DEFAULT_AGENT_MODEL,
            instructions="""Instructions for the agent...""",
            functions=[custom_tool1, custom_tool2],
            hooks=CustomAgentHooks()
        )
        
        self.description = "What this agent does"

# Create instance and export
custom_agent = CustomAgent()
__all__ = ["custom_agent", "CustomAgent"]
```

## Key Features

- **Agent System**: Extensible framework with specialized agents for different tasks
- **Conversation Management**: Thread-based conversations with history and context
- **Real-time Communication**: WebSocket-based messaging with streaming responses
- **Document Processing**: File upload, processing, and RAG (Retrieval Augmented Generation)
- **Authentication**: JWT-based auth with user and participant management

## Important Notes

- The application requires environment variables for configuration (see README)
- API documentation is available at `/docs` and `/redoc` when server is running
- WebSocket connections use the format: `ws://localhost:8000/ws/conversations/{conversation_id}`
- For agent interactions, use `@AGENT_NAME message` to target specific agents

## Frontend Architecture

### Application Structure
- Next.js 14 app directory structure with TypeScript
- Tailwind CSS for styling
- SWR for data fetching and caching

### Key Components

1. **WebSocket Hook** (`src/hooks/useWebSocket.ts`): Manages real-time connections to the backend, handles connection lifecycle, message sending/receiving, and token streaming.

2. **API Service** (`src/services/api.ts`): Axios-based API client with authentication interceptors for HTTP requests, including conversation management endpoints.

3. **Auth Context** (`src/context/AuthContext.tsx`): React context provider for authentication state management throughout the application.

4. **Conversation Components** (`src/components/conversation/`): UI components for displaying conversations, messages, and handling user input with agent interactions.

### Frontend-Backend Communication

1. **REST API**: Used for CRUD operations on conversations, users, and agents

2. **WebSockets**: Used for real-time messaging with:
   - Message streaming (token by token)
   - Typing indicators
   - Agent-specific routing via `@mentions`
   - Privacy mode support