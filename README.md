# Agent Framework

A multi-user, multi-agent collaborative workspace for business applications.

## Overview

Agent Framework is a simplified multi-agent system that provides a foundation for building collaborative AI workspaces. It includes the following specialized agents:

- **MODERATOR**: Routes queries to specialist agent experts
- **BUSINESS**: Provides business strategy and management advice
- **BUSINESSINTELLIGENCE**: Analyzes business data and provides metric insights
- **DATAANALYSIS**: Processes and interprets complex datasets
- **WEBSEARCH**: Searches the web for relevant information
- **DOCUMENTSEARCH**: Searches and analyzes uploaded documents
- **MONITOR**: Monitors agent activity and system health

## Project Structure

### Backend (FastAPI)

```
/backend
├── app/
│   ├── api/              # API endpoints and routes
│   │   ├── endpoints/    # API endpoint handlers
│   │   └── routes.py     # API route definitions
│   ├── core/             # Core configuration and utilities
│   │   ├── config.py     # Application configuration
│   │   └── security.py   # Authentication and security
│   ├── db/               # Database models and connections
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic schemas for validation
│   └── services/         # Business logic services
│       ├── agents/       # Agent implementations
│       │   ├── base_agent.py             # Common agent functionality
│       │   ├── moderator_agent.py        # Agent router
│       │   ├── business_agent.py         # Business strategy agent
│       │   ├── business_intelligence_agent.py  # BI agent 
│       │   ├── data_analysis_agent.py    # Data analysis agent
│       │   ├── web_search_agent.py       # Web search agent
│       │   ├── document_search_agent.py  # Document search agent
│       │   └── monitor_agent.py          # System monitoring agent
│       └── integrations/ # External service integrations
│           ├── google_drive_service.py   # Google Drive integration
│           └── onedrive_service.py       # OneDrive integration
└── tests/               # Test suite
```

### Frontend (Next.js)

```
/frontend
├── public/              # Static assets
├── src/
│   ├── app/             # Next.js app directory
│   │   ├── auth/        # Authentication pages
│   │   ├── conversations/  # Conversation pages
│   │   │   └── [id]/      # Specific conversation page
│   │   └── agents/       # Agent information pages
│   ├── components/       # React components
│   │   ├── layout/       # Layout components
│   │   ├── ui/           # UI components
│   │   ├── auth/         # Auth-related components
│   │   └── conversation/ # Conversation components
│   ├── context/          # React context providers
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utility functions
│   ├── services/         # API service clients
│   └── types/            # TypeScript type definitions
```

## Installation

### Prerequisites

- Node.js 18 or later
- Python 3.10 or later
- PostgreSQL database

### Backend Setup

1. Create a Python virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Copy the .env file to the correct location
cp .env.example .env
# Edit the .env file with your settings
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the development server:
```bash
uvicorn app.main:app --reload
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your settings
```

3. Start the development server:
```bash
npm run dev
```

## Usage

### Authentication

The system uses JWT-based authentication. Users can register and login through the web interface or API endpoints.

### Creating a Conversation

1. Login to the system
2. Navigate to "New Conversation"
3. Start interacting with the agents

### Agent Interaction

The MODERATOR agent automatically routes queries to the most appropriate specialist agent. Specialist agents have specific capabilities:

- **BUSINESS**: Strategic business advice
- **BUSINESSINTELLIGENCE**: Business metrics and KPI analysis
- **DATAANALYSIS**: Statistical analysis and data visualization
- **WEBSEARCH**: Internet search capabilities
- **DOCUMENTSEARCH**: Document retrieval and analysis
- **MONITOR**: System performance tracking

### Document Integration

Users can:
1. Connect Google Drive or OneDrive accounts
2. Import documents for analysis
3. Query documents using natural language

## Customization

### Adding New Agents

1. Create a new agent class in `backend/app/services/agents/`
2. Implement required methods and tools
3. Register the agent in `backend/app/services/agents/__init__.py`
4. Update frontend components to display the new agent

### Extending Functionality

- Add new API endpoints in `backend/app/api/endpoints/`
- Implement new frontend components in `frontend/src/components/`
- Update schemas and models as needed

## Environment Variables

### Backend

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

# LLM
OPENAI_API_KEY=your-openai-key

# Integrations
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
```

### Frontend

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_APP_NAME=Agent Framework
```

## License

[License information will be here]