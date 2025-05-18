# Agent Framework Backend

This is the backend application for the Agent Framework, built with FastAPI, SQLAlchemy, and LLM integrations (OpenAI, Anthropic).

## Getting Started

### Prerequisites

- Python 3.10 or later
- PostgreSQL database
- Virtual environment tool (venv, conda, etc.)

### Installation

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
cp .env.example .env
```

Edit `.env` with your settings (see the Configuration section below).

4. Run database migrations:

```bash
alembic upgrade head
```

5. Start the development server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at [http://localhost:8000](http://localhost:8000).

## Project Structure

```
app/
├── api/                # API endpoints and routes
│   ├── auth.py         # Authentication endpoints
│   ├── conversations.py # Conversation management
│   ├── websockets.py   # WebSocket endpoints
│   └── routes.py       # API route definitions
├── core/               # Core configuration and utilities
│   ├── buffer_manager.py # Conversation buffer management
│   ├── config.py       # Application configuration
│   ├── input_sanitizer.py # Security for prompt injection
│   ├── progress_manager.py # Progress reporting
│   ├── security.py     # Authentication and security
│   ├── text_splitter.py # Text processing
│   └── websocket_queue.py # WebSocket connection management
├── db/                 # Database models and connections
│   └── session.py      # Database session management
├── models/             # SQLAlchemy ORM models
│   └── domain/         # Domain models
│       └── models.py   # Database models
├── schemas/            # Pydantic schemas for validation
│   └── domain/         # Domain schemas
│       └── schemas.py  # API schemas
└── services/           # Business logic services
    ├── agents/         # Agent implementations
    │   ├── agent_interface.py     # Agent registry
    │   ├── agent_manager.py       # Agent orchestration
    │   ├── base_agent.py          # Base agent class
    │   ├── collaboration_manager.py # Multi-agent collaboration
    │   ├── common_context.py      # Shared context object
    │   ├── moderator_agent.py     # Moderator/router agent
    │   ├── business_agent.py      # Business strategy agent
    │   ├── business_intelligence_agent.py  # BI agent
    │   ├── data_analysis_agent.py # Data analysis agent
    │   ├── web_search_agent.py    # Web search agent
    │   ├── document_search_agent.py # Document search agent
    │   └── monitor_agent.py       # System monitoring agent
    ├── email_service.py        # Email notification service
    ├── memory/                 # Memory management
    │   └── conversation_buffer.py # Conversation history
    ├── notifications.py        # User notifications
    ├── rag/                    # Retrieval Augmented Generation
    │   └── storage_service.py  # Document storage and retrieval
    └── integrations/           # External service integrations
        ├── google_drive_service.py    # Google Drive integration
        └── onedrive_service.py        # OneDrive integration
```

## Key Features

### Agent System

- Base agent architecture for extensibility
- Moderator agent for query routing
- Specialized agents for different domains
- Agent registry and management
- Multi-agent collaboration

### Conversation Management

- Thread-based conversation structure
- Participant management and access control
- Message history and context tracking
- Privacy settings for sensitive conversations

### Authentication

- JWT-based authentication
- User and participant authentication flows
- Secure password hashing
- Email verification

### Real-time Communication

- WebSocket support for real-time messaging
- Message streaming for immediate feedback
- Typing indicators and connection management
- Progress tracking for long-running operations

### Document Processing

- File upload and processing
- External storage integrations
- Vector database for semantic search
- RAG (Retrieval Augmented Generation)

## Configuration

The application uses environment variables for configuration. The following variables are required:

```
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_framework

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Server
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
API_V1_STR=/api/v1

# LLM
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
DEFAULT_AGENT_MODEL=gpt-4o

# Storage
CHROMA_PERSIST_DIR=./data/chroma
BUFFER_SAVE_DIR=./data/buffers

# Email (optional)
SMTP_FROM_EMAIL=noreply@example.com
SMTP_FROM_NAME=Agent Framework
GMAIL_APP_PASSWORD=your-gmail-app-password

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Microsoft OAuth (optional)
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# RAG (optional)
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_DEFAULT_RETRIEVAL_K=4
```

## API Documentation

When the server is running, API documentation is available at:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Agent Development

### Creating a New Agent

1. Create a new file in `app/services/agents/` for your agent:

```python
from typing import Dict, List, Optional, Any, Union
import logging

from app.core.config import settings
from app.services.agents.base_agent import BaseAgent, AgentHooks, RunContextWrapper
from app.services.agents.common_context import CommonAgentContext

logger = logging.getLogger(__name__)

# Define domain-specific tools
async def custom_tool(param1: str, param2: Optional[str] = None) -> str:
    """
    Description of what this tool does.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2
        
    Returns:
        JSON string with results
    """
    # Tool implementation
    return "{}"

class CustomAgentHooks(AgentHooks):
    """Custom hooks for the custom agent."""

    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        await super().init_context(context)
        logger.info(f"Initialized context for CustomAgent")

class CustomAgent(BaseAgent):
    """
    Description of the custom agent's purpose.
    """
    
    def __init__(self, name="CUSTOM"):
        super().__init__(
            name=name,
            model=settings.DEFAULT_AGENT_MODEL,
            instructions="""Detailed instructions for the agent...""",
            functions=[custom_tool],
            hooks=CustomAgentHooks()
        )
        
        # Add description property
        self.description = "What this agent does"

# Create the agent instance
custom_agent = CustomAgent()

# Expose the agent for importing by other modules
__all__ = ["custom_agent", "CustomAgent"]
```

2. Register the agent in `app/services/agents/__init__.py`:

```python
from app.services.agents.custom_agent import custom_agent, CustomAgent

# Register with moderator
moderator_agent.register_agent(custom_agent)

# Register with agent interface
agent_interface.register_base_agent("CUSTOM", custom_agent)

# Update exports
__all__ = [
    # ... existing exports
    "custom_agent",
    "CustomAgent"
]
```

For more detailed instructions, refer to the [Domain Extension Guide](/DOMAIN_EXTENSION_GUIDE.md).

### Agent Interaction via WebSockets

Users can interact with agents through WebSocket connections:

```
WebSocket URL: ws://localhost:8000/ws/conversations/{conversation_id}
```

- Message format:
  - `@AGENT_NAME message` - Direct message to a specific agent
  - `@ message` - Let the moderator choose the most appropriate agent
  - `?` - Show help message
  - Regular messages without `@` are broadcast to all participants

- Response format:
  - Messages with agent responses
  - Typing indicators
  - Token-by-token streaming for real-time feedback

## Testing

Run tests with:

```bash
pytest
```

For specific test files:

```bash
pytest tests/test_api/test_auth.py
```

With coverage:

```bash
pytest --cov=app tests/
```