# Agent Framework

A multi-user, multi-agent discussion platform enabling collaborative conversations with specialized AI agents. Agent Framework facilitates real-time interactions between human participants and AI experts across various domains including legal, financial, and technical advisors.

## System Architecture

### Data Model
```mermaid
erDiagram
    User ||--o{ Thread : "owns"
    User ||--o{ MessageReadReceipt : "reads"
    Thread ||--|{ Message : "contains"
    Thread ||--|{ ThreadParticipant : "has"
    Thread ||--|{ ThreadAgent : "has"
    ThreadParticipant ||--o{ Message : "sends"
    ThreadAgent ||--o{ Message : "generates"
    Message ||--o{ MessageReadReceipt : "has"
    Message ||--o{ Message : "replies_to"
```

### System Flow
```mermaid
flowchart TD
    User[Human User] --> Auth[Authentication]
    Auth -->|JWT Token| API[FastAPI Backend]
    Auth --> |JWT Token| WS[WebSocket Connection]
    
    API --> |CRUD| DB[(PostgreSQL)]
    WS --> |Real-time| MS[Message Service]
    
    subgraph Backend
        API
        WS
        MS --> AS[Agent Service]
        AS --> |OpenAI API| AI[AI Agents]
    end
```

## Features

- Multi-user chat threads with real-time updates
- Specialized AI agents (Legal, Financial, Technical advisors)
- WebSocket-based real-time communication
- Message persistence and history
- Role-based access control
- Thread-based discussions
- Coordinated agent responses

## Project Structure

### Backend Structure
```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── conversations.py
│   │   ├── messages.py
│   │   └── websockets.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   └── websocket_manager.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py
│   ├── models/
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   └── models.py
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py
│   │   └── __init__.py
│   ├── services/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   └── agent_service.py
│   │   ├── __init__.py
│   │   ├── message_service.py
│   │   └── notifications.py
│   ├── templates/
│   │   └── email/
│   │       └── thread_invitation.html
│   └── __init__.py
├── tests/
│   └── __init__.py
└── utils/
    ├── test_startup.py
    └── verify_imports.py
```

### Frontend Structure
```
frontend/
├── README.md
├── components.json
├── next.config.js
├── package-lock.json
├── package.json
├── postcss.config.mjs
├── tailwind.config.js
├── tailwind.config.ts
├── tsconfig.json
├── public/
│   ├── file.svg
│   ├── globe.svg
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg
└── src/
    ├── app/
    │   ├── conversations/
    │   │   ├── [id]/
    │   │   │   ├── components/
    │   │   │   │   ├── DateSeparator.tsx
    │   │   │   │   ├── MessageInput.tsx
    │   │   │   │   ├── MessageItem.tsx
    │   │   │   │   ├── MessageList.tsx
    │   │   │   │   ├── SystemStatus.tsx
    │   │   │   │   ├── TypingIndicator.tsx
    │   │   │   │   └── index.ts
    │   │   │   ├── hooks/
    │   │   │   │   ├── index.ts
    │   │   │   │   ├── useConversation.ts
    │   │   │   │   ├── useMessageLoader.ts
    │   │   │   │   ├── useScrollManager.ts
    │   │   │   │   ├── useTypingIndicator.ts
    │   │   │   │   └── useWebSocket.ts
    │   │   │   ├── types/
    │   │   │   │   ├── index.ts
    │   │   │   │   ├── message.types.ts
    │   │   │   │   ├── messages.ts
    │   │   │   │   ├── state.types.ts
    │   │   │   │   └── websocket.types.ts
    │   │   │   ├── utils/
    │   │   │   │   ├── date.utils.ts
    │   │   │   │   ├── format.utils.ts
    │   │   │   │   ├── index.ts
    │   │   │   │   └── message.utils.ts
    │   │   │   └── page.tsx
    │   │   ├── new/
    │   │   │   └── page.tsx
    │   │   └── page.tsx
    │   ├── fonts/
    │   │   ├── GeistMonoVF.woff
    │   │   └── GeistVF.woff
    │   ├── login/
    │   │   └── page.tsx
    │   ├── register/
    │   │   └── page.tsx
    │   ├── favicon.ico
    │   ├── globals.css
    │   ├── layout.tsx
    │   └── page.tsx
    ├── components/
    │   ├── auth/
    │   │   ├── LoginForm.tsx
    │   │   └── RegisterForm.tsx
    │   ├── conversation/
    │   │   └── ConversationList.tsx
    │   ├── layout/
    │   │   ├── ClientLayout.tsx
    │   │   ├── Footer.tsx
    │   │   ├── Header.tsx
    │   │   └── MainLayout.tsx
    │   └── ui/
    │       ├── alert.tsx
    │       ├── button.tsx
    │       ├── card.tsx
    │       ├── error-alert.tsx
    │       ├── input.tsx
    │       ├── textarea.tsx
    │       ├── textarea.ui
    │       ├── toast.tsx
    │       ├── toaster.tsx
    │       └── use-toast.ts
    ├── context/
    │   └── AuthContext.tsx
    ├── lib/
    │   ├── utils.ts
    │   └── validation.ts
    ├── services/
    │   ├── api.ts
    │   ├── auth.ts
    │   ├── conversations.ts
    │   └── websocket.ts
    ├── types/
    │   ├── conversation.ts
    │   └── index.ts
    └── middleware.ts
```

## Setup

### Backend Requirements

- Python 3.9+
- PostgreSQL
- Redis (for WebSocket state)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb cyberiad
alembic upgrade head

# Start server
uvicorn cyberiad.main:app --reload
```

### Frontend Requirements

- Node.js 18+
- npm/yarn

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/cyberiad
JWT_SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Agent System

### Available Agent Types
- MODERATOR
- DOCTOR
- LAWYER
- ACCOUNTANT
- ETHICIST
- ENVIRONMENTAL_SCIENTIST
- FINANCIER
- BUSINESSMAN

Each agent type has specific expertise and role definitions, with responses coordinated through the agent service.

## Development

- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- API documentation: `http://localhost:8000/docs`
- Database migrations: Managed via Alembic
- Code style: PEP-8 compliant Python, standard TypeScript/React practices

### Testing

```bash
# Backend tests
pytest src/tests

# Frontend tests
npm test
```

## Current Status

### Completed
- Authentication system
- Database schema and relationships
- Conversation management
- Type system
- Core frontend components

### In Progress
- Real-time messaging system
- Email notifications
- Agent integration
- Security enhancements

### Pending
- Production deployment
- Enhanced moderation features
- Advanced agent capabilities

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
