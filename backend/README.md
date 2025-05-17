# Agent Framework Backend

This is the backend application for the Agent Framework, built with FastAPI, SQLAlchemy, and the OpenAI SDK.

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
│   ├── endpoints/      # API endpoint handlers
│   │   ├── auth.py     # Authentication endpoints
│   │   ├── agents.py   # Agent-related endpoints
│   │   └── ...         # Other endpoint modules
│   └── routes.py       # API route definitions
├── core/               # Core configuration and utilities
│   ├── config.py       # Application configuration
│   ├── security.py     # Authentication and security
│   └── logging.py      # Logging configuration
├── db/                 # Database models and connections
│   ├── session.py      # Database session management
│   └── base.py         # Base model class
├── models/             # SQLAlchemy ORM models
│   ├── user.py         # User model
│   ├── conversation.py # Conversation model
│   └── ...             # Other models
├── schemas/            # Pydantic schemas for validation
│   ├── user.py         # User schemas
│   ├── agent.py        # Agent schemas
│   └── ...             # Other schemas
└── services/           # Business logic services
    ├── agents/         # Agent implementations
    │   ├── base_agent.py              # Base agent class
    │   ├── agent_interface.py         # Agent management interface
    │   ├── common_context.py          # Shared context object
    │   ├── moderator_agent.py         # Moderator/router agent
    │   ├── business_agent.py          # Business strategy agent
    │   ├── business_intelligence_agent.py  # BI agent
    │   ├── data_analysis_agent.py     # Data analysis agent
    │   ├── web_search_agent.py        # Web search agent
    │   ├── document_search_agent.py   # Document search agent
    │   └── monitor_agent.py           # System monitoring agent
    ├── integrations/   # External service integrations
    │   ├── google_drive_service.py    # Google Drive integration
    │   └── onedrive_service.py        # OneDrive integration
    ├── memory/         # Memory and context management
    │   └── memory_service.py          # Conversation memory service
    └── rag/            # Retrieval-augmented generation
        └── rag_service.py             # RAG implementation
```

## Key Features

### Agent System

- Base agent architecture for extensibility
- Moderator agent for query routing
- Specialized agents for different domains
- Agent registry and management

### Authentication

- JWT-based authentication
- Role-based access control
- Secure password hashing

### Real-time Communication

- WebSocket support for real-time messaging
- Message streaming for long-running operations

### Document Processing

- File upload and processing
- Google Drive integration
- OneDrive integration
- Vector search for document retrieval

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
WS_URL=ws://localhost:8000/ws
API_URL=http://localhost:8000

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_CONNECTION_TIMEOUT=3600

# OpenAI
OPENAI_API_KEY=your-openai-key
DEFAULT_AGENT_MODEL=gpt-4o

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# RAG
CHROMA_PERSIST_DIR=/path/to/chroma_db
BUFFER_SAVE_DIR=/path/to/buffers
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

# Placeholder for function_tool decorator
def function_tool(func):
    return func

class CustomAgentHooks(AgentHooks):
    """Custom hooks for the custom agent."""

    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        await super().init_context(context)
        logger.info(f"Initialized context for CustomAgent")

@function_tool
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

class CustomAgent(BaseAgent):
    """
    Description of the custom agent's purpose.
    """
    
    def __init__(self, name="CUSTOM"):
        super().__init__(
            name=name,
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

### Agent Tools

Tools are functions that can be called by the agent to perform specific actions. To create a new tool:

1. Define the tool using the `function_tool` decorator
2. Implement the tool functionality
3. Add the tool to the agent's functions list

Example:

```python
@function_tool
async def analyze_data(data: str, analysis_type: Optional[str] = "basic") -> str:
    """
    Analyze provided data.
    
    Args:
        data: The data to analyze
        analysis_type: Type of analysis to perform
        
    Returns:
        JSON string with analysis results
    """
    # Tool implementation here
    return json.dumps({"result": "analysis"})

# Add to agent
my_agent = MyAgent(
    name="MY_AGENT",
    functions=[analyze_data]
)
```

## Testing

Run tests with:

```bash
pytest
```

For specific test files:

```bash
pytest tests/test_api/test_endpoints/test_auth.py
```

With coverage:

```bash
pytest --cov=app tests/
```