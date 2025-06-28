# Thanotopolis - Next-Generation AI Voice Agent Platform

A comprehensive multi-agent AI platform built by **Cyberiad.ai** that revolutionizes telephone answering services with **Deepgram Voice Agent** integration, advanced agent collaboration, and sophisticated multi-tenant architecture.

## 🎙️ Revolutionary Voice Agent Technology

### **Deepgram Voice Agent Integration** - The Future of Telephony AI

Thanotopolis has pioneered the integration of **Deepgram's Voice Agent API** - a breakthrough technology that replaces traditional STT → LLM → TTS pipelines with a unified, real-time conversational AI system.

#### **Before vs After: Architectural Revolution**

**Legacy Architecture** (Pre-Voice Agent):
```
Twilio → Deepgram STT → OpenAI GPT → ElevenLabs TTS → Audio Conversion → Twilio
Latency: 2-5 seconds | Complexity: 3 separate APIs | Format: MP3→mulaw conversion
```

**Voice Agent Architecture** (Current):
```
Twilio ↔ Deepgram Voice Agent (STT + LLM + TTS unified) ↔ Twilio
Latency: <500ms | Complexity: Single WebSocket | Format: Native mulaw
```

#### **Performance Breakthrough**
- **🚀 90% Latency Reduction**: From 2-5 seconds to <500ms response time
- **🎯 Native Audio**: Direct mulaw support eliminates conversion overhead
- **💡 Unified Processing**: Single WebSocket replaces multiple API calls
- **⚡ Real-time Streaming**: Continuous conversation flow with immediate responses

### **Consent-Based Agent Collaboration**

Revolutionary integration combining Voice Agent's real-time capabilities with our 20+ specialist agents:

#### **How It Works**
1. **Smart Detection**: AI analyzes query complexity in real-time
2. **User Consent**: "I can give you a quick response, or consult with my specialist team. This will take about 30 seconds."
3. **Expert Collaboration**: Routes to MODERATOR + specialist agents (Cultural, Compliance, Financial, etc.)
4. **Seamless Handoff**: Returns enhanced knowledge to voice conversation

#### **Specialist Agent Network**
- **Cultural Agents**: 17 culturally-sensitive agents (Mexican, Filipino, Vietnamese, Korean, Jewish, Persian, etc.)
- **Service Agents**: Financial, Compliance, Emergency, Inventory, Grief Support
- **Technical Agents**: Web Search, Regulatory, Documentation

## 📢 What's New (June 2025)

### **Revolutionary Updates**
- **🎙️ Deepgram Voice Agent**: Complete telephony architecture overhaul with 90% latency reduction
- **🤖 Voice-Agent Collaboration**: Consent-based specialist agent integration for complex queries
- **📊 Advanced Call Analytics**: Message-based call tracking with granular transcript analysis
- **🔄 A/B Testing Infrastructure**: Feature flag system for safe Voice Agent rollout
- **🎯 Production Ready**: 100% Voice Agent rollout with instant rollback capability

### **Enhanced Features**
- **Enhanced Call Message System**: Granular message tracking replacing monolithic transcripts
- **17 New Cultural Agents**: Culturally-sensitive funeral and memorial service agents
- **Improved Test Coverage**: From 63% to 72% with 98.4% test success rate
- **Voice Agent Testing Tools**: Comprehensive testing suite for Voice Agent connections

## 🏗️ Architecture Overview

### **Backend Technology Stack** (`/backend`)
- **🌐 Framework**: FastAPI with async/await architecture
- **🗄️ Database**: PostgreSQL 14+ with pgvector for RAG capabilities
- **🎙️ Voice Processing**: Deepgram Voice Agent API (STT + LLM + TTS unified)
- **🤖 AI Integration**: GPT-4o-mini with 20+ specialist agents
- **☎️ Telephony**: Twilio integration with WebSocket streaming
- **🔐 Authentication**: JWT-based with hierarchical role system
- **🧪 Testing**: Comprehensive unit and integration test suite (72% coverage)

### **Frontend Technology Stack** (`/frontend`)
- **⚛️ Framework**: Next.js 14 with TypeScript
- **🎨 UI/UX**: Tailwind CSS with custom component library
- **⚡ Real-time**: WebSocket connections for live conversations
- **🎤 Voice**: Browser-based audio recording and playbook
- **📊 State Management**: React Context with custom hooks
- **🧪 Testing**: Jest with React Testing Library

### **Database Schema & E/R Diagram**

```mermaid
erDiagram
    TENANTS ||--o{ USERS : owns
    TENANTS ||--o{ CONVERSATIONS : hosts
    TENANTS ||--o{ AGENTS : owns
    TENANTS ||--|| TELEPHONY_CONFIGURATIONS : has
    
    TELEPHONY_CONFIGURATIONS ||--o{ PHONE_CALLS : receives
    TELEPHONY_CONFIGURATIONS ||--o{ PHONE_VERIFICATION_ATTEMPTS : has
    
    PHONE_CALLS ||--o{ CALL_MESSAGES : contains
    PHONE_CALLS ||--o{ CALL_AGENTS : uses
    PHONE_CALLS }o--|| CONVERSATIONS : links_to
    
    CONVERSATIONS ||--o{ MESSAGES : contains
    CONVERSATIONS ||--o{ CONVERSATION_USERS : has
    CONVERSATIONS ||--o{ CONVERSATION_PARTICIPANTS : includes
    
    USERS ||--o{ MESSAGES : sends
    USERS ||--o{ CONVERSATIONS : creates
    USERS ||--o{ USAGE_RECORDS : generates
    USERS ||--o{ DOCUMENT_EMBEDDINGS : owns
    
    AGENTS ||--o{ CALL_AGENTS : participates_in
    
    TENANTS {
        uuid id PK
        string name
        string subdomain UK
        string access_code
        string description
        string full_name
        json address
        string phone
        string organization_email
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }
    
    TELEPHONY_CONFIGURATIONS {
        uuid id PK
        uuid tenant_id FK
        string organization_phone_number
        string platform_phone_number
        string verification_status
        boolean call_forwarding_enabled
        text welcome_message
        json business_hours
        string timezone
        json voice_settings
        boolean record_calls
        timestamp created_at
        timestamp updated_at
    }
    
    PHONE_CALLS {
        uuid id PK
        uuid telephony_config_id FK
        uuid conversation_id FK
        string call_sid UK
        string customer_phone_number
        string organization_phone_number
        string platform_phone_number
        string direction
        string status
        timestamp start_time
        timestamp answer_time
        timestamp end_time
        integer duration_seconds
        integer cost_cents
        string recording_url
        text summary
        json call_metadata
    }
    
    CALL_MESSAGES {
        uuid id PK
        uuid call_id FK
        text content
        json sender
        timestamp timestamp
        string message_type
        jsonb message_metadata
        timestamp created_at
        timestamp updated_at
    }
    
    AGENTS {
        uuid id PK
        uuid owner_tenant_id FK
        string agent_type UK
        string name
        text description
        boolean is_enabled
        boolean is_free_agent
        string owner_domain
        json capabilities
        timestamp created_at
        timestamp updated_at
    }
    
    USERS {
        uuid id PK
        uuid tenant_id FK
        string email
        string username
        string hashed_password
        string first_name
        string last_name
        boolean is_active
        boolean is_verified
        string role
        timestamp created_at
        timestamp updated_at
    }
    
    CONVERSATIONS {
        uuid id PK
        uuid tenant_id FK
        uuid created_by_user_id FK
        string title
        text description
        string status
        timestamp created_at
        timestamp updated_at
    }
    
    MESSAGES {
        uuid id PK
        uuid conversation_id FK
        uuid user_id FK
        uuid participant_id FK
        string message_type
        text content
        string agent_type
        json message_metadata
        timestamp created_at
        timestamp updated_at
    }
    
    USAGE_RECORDS {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        uuid conversation_id FK
        string usage_type
        numeric amount
        numeric cost_per_unit
        integer cost_cents
        string service_provider
        string model_name
        json usage_metadata
        timestamp usage_date
        timestamp created_at
    }
```

### **Backend Code Structure**

```
backend/
├── app/
│   ├── agents/                          # 🤖 AI Agent System
│   │   ├── base_agent.py               # Base agent interface
│   │   ├── moderator_agent.py          # Central routing agent
│   │   ├── collaboration_manager.py    # Multi-agent collaboration
│   │   ├── agent_manager.py            # Agent discovery & lifecycle
│   │   ├── tenant_aware_agent_manager.py # Multi-tenant agent filtering
│   │   │
│   │   ├── # 🌍 Cultural Specialist Agents (17 agents)
│   │   ├── mexican_cultural_agent.py   # Mexican traditions & Day of the Dead
│   │   ├── filipino_cultural_agent.py  # Filipino wake & burial customs
│   │   ├── vietnamese_cultural_agent.py # Vietnamese ancestor veneration
│   │   ├── korean_cultural_agent.py    # Korean funeral rites
│   │   ├── jewish_cultural_agent.py    # Jewish burial & shiva traditions
│   │   ├── persian_cultural_agent.py   # Persian/Iranian customs
│   │   ├── thai_cultural_agent.py      # Thai Buddhist practices
│   │   ├── cambodian_cultural_agent.py # Cambodian memorial traditions
│   │   ├── russian_cultural_agent.py   # Russian Orthodox customs
│   │   ├── ukrainian_cultural_agent.py # Ukrainian memorial services
│   │   ├── japanese_cultural_agent.py  # Japanese Buddhist & Shinto
│   │   ├── somali_cultural_agent.py    # Somali Islamic traditions
│   │   ├── ethiopian_cultural_agent.py # Ethiopian Orthodox customs
│   │   ├── chinese_cultural_agent.py   # Chinese ancestor worship
│   │   ├── polish_cultural_agent.py    # Polish Catholic traditions
│   │   ├── armenian_cultural_agent.py  # Armenian Apostolic customs
│   │   ├── salvadoran_cultural_agent.py # Salvadoran traditions
│   │   │
│   │   ├── # 🏢 Service Specialist Agents
│   │   ├── demo_answering_service_agent.py # Barney (Cyberiad.ai)
│   │   ├── financial_services_agent.py     # Payment plans & billing
│   │   ├── compliance_and_documentation_agent.py # Regulatory compliance
│   │   ├── emergency_and_crisis_agent.py   # Crisis & urgent situations
│   │   ├── inventory_and_facilities_agent.py # Facilities management
│   │   ├── grief_support_agent.py          # Emotional support
│   │   ├── regulatory_agent.py             # Legal & regulatory
│   │   ├── religious_agent.py              # Religious services
│   │   └── web_search_agent.py             # Real-time information
│   │
│   ├── api/                            # 🌐 REST API Endpoints
│   │   ├── auth.py                     # Authentication & user management
│   │   ├── conversations.py            # Chat & message handling
│   │   ├── agents.py                   # Agent discovery & configuration
│   │   ├── organizations.py            # Multi-tenant management
│   │   ├── billing.py                  # Usage tracking & payments
│   │   ├── telephony.py                # Legacy telephony API
│   │   ├── telephony_voice_agent.py    # 🎙️ Voice Agent WebSocket handler
│   │   ├── telephony_websocket.py      # Legacy telephony WebSocket
│   │   ├── voice_streaming.py          # Voice chat API
│   │   ├── streaming_stt.py            # Legacy STT streaming
│   │   ├── websockets.py               # General WebSocket management
│   │   └── admin.py                    # Admin panel APIs
│   │
│   ├── services/                       # 🔧 Core Business Logic
│   │   ├── voice/                      # 🎙️ Voice Processing Services
│   │   │   ├── deepgram_voice_agent.py # Voice Agent WebSocket client
│   │   │   ├── voice_agent_collaboration.py # Specialist agent integration
│   │   │   ├── deepgram_service.py     # Legacy STT service
│   │   │   ├── elevenlabs_service.py   # Legacy TTS service
│   │   │   └── audio_converter.py      # Audio format utilities
│   │   │
│   │   ├── rag/                        # 📚 Retrieval Augmented Generation
│   │   │   ├── ingestion_service.py    # Document processing
│   │   │   ├── pgvector_storage_service.py # Vector storage
│   │   │   └── pgvector_query_service.py   # Semantic search
│   │   │
│   │   ├── memory/                     # 🧠 Conversation Memory
│   │   │   ├── conversation_buffer.py  # Message buffering
│   │   │   └── conversation_context_manager.py # Context management
│   │   │
│   │   ├── telephony_service.py        # Legacy telephony logic
│   │   ├── billing_automation.py       # Automated billing & usage
│   │   ├── usage_service.py            # Usage tracking & metrics
│   │   ├── monitoring_service.py       # System monitoring
│   │   └── context_manager.py          # Request context management
│   │
│   ├── models/                         # 🗄️ Database Models
│   │   └── models.py                   # Complete SQLAlchemy schema
│   │
│   ├── schemas/                        # 📋 Pydantic Schemas
│   │   └── schemas.py                  # API request/response models
│   │
│   ├── core/                           # ⚡ Core Utilities
│   │   ├── config.py                   # Configuration management
│   │   ├── buffer_manager.py           # Audio buffer management
│   │   ├── websocket_queue.py          # WebSocket message queuing
│   │   ├── input_sanitizer.py          # Input validation & sanitization
│   │   └── common_calculator.py        # Utility calculations
│   │
│   ├── db/                            # 🗄️ Database Configuration
│   │   └── database.py                 # Database connection & session
│   │
│   ├── auth/                          # 🔐 Authentication
│   │   └── auth.py                     # JWT & security utilities
│   │
│   ├── tasks/                         # ⏰ Background Tasks
│   │   └── telephony_cleanup.py       # Call cleanup & maintenance
│   │
│   └── main.py                        # 🚀 FastAPI application entry
│
├── tests/                             # 🧪 Test Suite (72% coverage)
│   ├── unit/                          # Unit tests
│   ├── integration/                   # Integration tests
│   ├── fixtures/                      # Test fixtures
│   └── conftest.py                    # Test configuration
│
├── alembic/                           # 📊 Database Migrations
│   └── versions/                      # Migration scripts
│
├── additional_tests/                  # 🔬 Development Tests
│   ├── test_voice_agent.py           # Voice Agent connectivity
│   ├── debug_voice_agent_events.py   # Real-time event monitoring
│   └── test_deepgram_*.py            # Deepgram service tests
│
├── requirements.txt                   # 📦 Python dependencies
├── run.py                            # 🏃 Development server
├── gunicorn_config.py                # 🌐 Production server config
└── alembic.ini                       # 📊 Migration configuration
```

### **Frontend Code Structure**

```
frontend/
├── src/
│   ├── app/                           # 📱 Next.js App Router
│   │   ├── conversations/             # 💬 Chat Interface
│   │   │   ├── [id]/                  # Individual conversation
│   │   │   │   ├── components/        # Chat UI components
│   │   │   │   │   ├── MessageList.tsx
│   │   │   │   │   ├── MessageInput.tsx
│   │   │   │   │   ├── VoiceControls.tsx
│   │   │   │   │   ├── LanguageSelector.tsx
│   │   │   │   │   ├── StreamingIndicator.tsx
│   │   │   │   │   └── TypingIndicator.tsx
│   │   │   │   ├── hooks/             # Chat-specific hooks
│   │   │   │   │   ├── useConversation.ts
│   │   │   │   │   ├── useVoice.ts
│   │   │   │   │   ├── useWebSocket.ts
│   │   │   │   │   └── useMessageLoader.ts
│   │   │   │   ├── types/             # TypeScript definitions
│   │   │   │   │   ├── message.types.ts
│   │   │   │   │   └── websocket.types.ts
│   │   │   │   └── page.tsx           # Conversation page
│   │   │   ├── new/page.tsx           # New conversation
│   │   │   └── page.tsx               # Conversation list
│   │   │
│   │   ├── organizations/             # 🏢 Multi-Tenant Management
│   │   │   ├── telephony/             # ☎️ Telephony Management
│   │   │   │   ├── setup/page.tsx     # Telephony setup wizard
│   │   │   │   ├── calls/             # 📞 Call Management
│   │   │   │   │   ├── [id]/page.tsx  # Individual call details
│   │   │   │   │   ├── components/    # Call UI components
│   │   │   │   │   │   ├── CallMessagesList.tsx
│   │   │   │   │   │   ├── CallMessageItem.tsx
│   │   │   │   │   │   └── CallMessageGroup.tsx
│   │   │   │   │   ├── hooks/         # Call-specific hooks
│   │   │   │   │   │   └── useCallMessages.ts
│   │   │   │   │   └── page.tsx       # Call list
│   │   │   │   ├── active-calls/page.tsx # Live call monitoring
│   │   │   │   ├── analytics/page.tsx # Call analytics
│   │   │   │   ├── test/page.tsx      # Telephony testing
│   │   │   │   └── components/        # Telephony components
│   │   │   │       ├── PhoneVerificationModal.tsx
│   │   │   │       ├── BusinessHoursEditor.tsx
│   │   │   │       └── ForwardingInstructionsModal.tsx
│   │   │   ├── admin/page.tsx         # Organization admin
│   │   │   ├── members/page.tsx       # Member management
│   │   │   ├── edit/page.tsx          # Organization settings
│   │   │   └── new/page.tsx           # New organization
│   │   │
│   │   ├── billing/page.tsx           # 💳 Billing & Usage
│   │   ├── login/page.tsx             # 🔐 Authentication
│   │   ├── register/page.tsx          # 📝 User registration
│   │   ├── greeting/page.tsx          # 👋 Welcome page
│   │   ├── layout.tsx                 # 🎨 Root layout
│   │   ├── globals.css                # 🎨 Global styles
│   │   └── page.tsx                   # 🏠 Dashboard
│   │
│   ├── components/                    # 🧩 Reusable Components
│   │   ├── ui/                        # 🎨 UI Component Library
│   │   │   ├── button.tsx             # Button component
│   │   │   ├── input.tsx              # Input fields
│   │   │   ├── dialog.tsx             # Modal dialogs
│   │   │   ├── table.tsx              # Data tables
│   │   │   ├── card.tsx               # Card layouts
│   │   │   ├── tabs.tsx               # Tab navigation
│   │   │   └── use-toast.tsx          # Toast notifications
│   │   │
│   │   ├── telephony/                 # ☎️ Telephony Components
│   │   │   ├── TelephonySystemInitializer.tsx
│   │   │   └── TelephonyTestPanel.tsx
│   │   │
│   │   ├── navigation/                # 🧭 Navigation
│   │   │   └── OrganizationNavigation.tsx
│   │   │
│   │   ├── MainLayout.tsx             # 🏗️ Layout wrapper
│   │   ├── ProtectedRoute.tsx         # 🔐 Route protection
│   │   ├── BillingDashboard.tsx       # 💳 Billing UI
│   │   ├── SubscriptionPlans.tsx      # 📋 Subscription plans
│   │   ├── SuperAdminBilling.tsx      # 👑 Admin billing
│   │   └── WingedSolarIcon.tsx        # 🦅 Brand icon
│   │
│   ├── services/                      # 🔧 Frontend Services
│   │   ├── telephony/                 # ☎️ Telephony Services
│   │   │   ├── TelephonyCallManager.ts
│   │   │   ├── TelephonyWebSocketManager.ts
│   │   │   ├── TelephonyErrorHandler.ts
│   │   │   ├── TelephonyTTSSTTProcessor.ts
│   │   │   ├── IncomingCallHandler.ts
│   │   │   └── TwilioAudioService.ts
│   │   │
│   │   ├── voice/                     # 🎤 Voice Services
│   │   │   ├── StreamingSpeechToTextService.ts
│   │   │   ├── TelephonyStreamingService.ts
│   │   │   ├── AdvancedLanguageDetection.ts
│   │   │   └── voiceConfig.ts
│   │   │
│   │   ├── api.ts                     # 🌐 API client
│   │   ├── conversations.ts           # 💬 Conversation API
│   │   ├── telephony.ts               # ☎️ Telephony API
│   │   ├── websocket.ts               # 🔌 WebSocket client
│   │   └── admin.ts                   # 👑 Admin API
│   │
│   ├── contexts/                      # 🔄 React Contexts
│   │   └── AuthContext.tsx            # 🔐 Authentication context
│   │
│   ├── hooks/                         # 🪝 Custom React Hooks
│   │   └── useActiveCall.ts           # ☎️ Active call management
│   │
│   ├── lib/                           # 📚 Utilities
│   │   ├── utils.ts                   # General utilities
│   │   ├── circuitBreaker.ts          # Error handling
│   │   ├── requestQueue.ts            # Request management
│   │   └── participantStorage.ts      # Call participant storage
│   │
│   ├── types/                         # 📝 TypeScript Definitions
│   │   ├── conversation.ts            # Conversation types
│   │   └── user.types.ts              # User types
│   │
│   └── middleware.ts                  # 🛡️ Route middleware
│
├── public/                            # 📁 Static Assets
│   ├── favicon.ico                    # Site icon
│   └── winged-solar-disk.png          # Brand logo
│
├── __tests__/                         # 🧪 Frontend Tests
│   ├── App.integration.test.js        # Integration tests
│   ├── AuthContext.test.js            # Authentication tests
│   ├── Dashboard.test.js              # Dashboard tests
│   └── Login.test.js                  # Login tests
│
├── package.json                       # 📦 Dependencies & scripts
├── next.config.js                     # ⚙️ Next.js configuration
├── tailwind.config.js                 # 🎨 Tailwind CSS config
├── tsconfig.json                      # 📝 TypeScript config
└── jest.config.js                     # 🧪 Jest test config
```

## 🚀 Quick Start

### **Prerequisites**
- **Python 3.11+** (Backend)
- **Node.js 18+** (Frontend)
- **PostgreSQL 14+** (Database with pgvector extension)
- **Redis** (Caching & session management)
- **Deepgram API Key** (Voice Agent)
- **Twilio Account** (Telephony)

### **Backend Setup**

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env with your API keys:
#   DEEPGRAM_API_KEY=your_deepgram_key
#   TWILIO_ACCOUNT_SID=your_twilio_sid
#   TWILIO_AUTH_TOKEN=your_twilio_token
#   DATABASE_URL=postgresql://user:pass@localhost:5432/thanotopolis

# Database setup
alembic upgrade head

# Create admin user
python create_admin_user.py

# Start development server
python run.py
```

### **Frontend Setup**

```bash
cd frontend

# Install Node dependencies
npm install

# Environment configuration
cp .env.local.example .env.local
# Edit .env.local:
#   NEXT_PUBLIC_API_URL=http://localhost:8000
#   NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Start development server
npm run dev
```

### **Voice Agent Configuration**

```bash
# Backend environment variables
USE_VOICE_AGENT=true                    # Enable Voice Agent
VOICE_AGENT_ROLLOUT_PERCENTAGE=100      # 100% rollout
VOICE_AGENT_LISTENING_MODEL=nova-3      # STT model
VOICE_AGENT_THINKING_MODEL=gpt-4o-mini  # LLM model
VOICE_AGENT_SPEAKING_MODEL=aura-2-thalia-en # TTS voice
```

## ☎️ Telephony System Features

### **🎙️ Deepgram Voice Agent**
- **Unified Processing**: STT + LLM + TTS in single WebSocket
- **Ultra-Low Latency**: <500ms response time (90% improvement)
- **Native Audio**: Direct mulaw support for telephony
- **Real-time Streaming**: Continuous conversation flow
- **Auto-Greetings**: Immediate call engagement

### **🤖 Agent Collaboration**
- **Consent-Based**: User chooses when to access specialist expertise
- **20+ Specialist Agents**: Cultural, regulatory, financial, emergency
- **Seamless Handoff**: Expert knowledge integrated into voice conversation
- **Graceful Fallback**: Clear error handling and timeout management

### **📞 Call Management**
- **Call Forwarding**: Organizations keep existing numbers
- **Multi-language Support**: Automatic language detection
- **Real-time Analytics**: Live call monitoring and metrics
- **Message-Based Transcripts**: Granular conversation tracking
- **Recording & Transcription**: Automated call documentation

### **How Telephony Works**
1. **Customer calls** organization's existing number
2. **Call forwards** to platform's Twilio number
3. **Voice Agent answers** with personalized greeting
4. **Real-time conversation** with specialist agent collaboration
5. **Call analytics** and transcript automatically generated

## 🌐 API Architecture

### **Core API Endpoints**
- **`/api/auth/*`** - Authentication & user management
- **`/api/conversations/*`** - Chat & message handling
- **`/api/agents/*`** - Agent discovery & configuration
- **`/api/telephony/*`** - Phone system integration
- **`/api/organizations/*`** - Multi-tenant management
- **`/api/billing/*`** - Usage tracking & payments

### **Real-time WebSocket Endpoints**
- **`/api/ws/conversation/{id}`** - Chat conversations
- **`/api/ws/telephony/voice-agent/stream`** - 🎙️ Voice Agent streaming
- **`/api/ws/telephony/stream/{call_id}`** - Legacy telephony streaming
- **`/api/ws/voice/{conversation_id}`** - Voice chat

### **Call Message APIs**
- **`GET /api/telephony/calls/{call_id}/messages`** - Retrieve call messages
- **`POST /api/telephony/calls/{call_id}/messages`** - Add call messages
- **`PATCH /api/telephony/calls/{call_id}/messages/{message_id}`** - Update messages
- **`DELETE /api/telephony/calls/{call_id}/messages/{message_id}`** - Delete messages

## 🤖 AI Agent Ecosystem

### **Agent Architecture**
```python
# Agent ownership models
class BaseAgent:
    OWNER_DOMAINS = []          # Free agent (all organizations)
    OWNER_DOMAINS = ["demo"]    # Proprietary (specific org)
    OWNER_DOMAINS = ["demo", "enterprise"]  # Multi-organization
```

### **Cultural Agents (17 Specialized)**
- **🇲🇽 Mexican**: Traditional customs & Day of the Dead
- **🇵🇭 Filipino**: Wake & burial traditions
- **🇻🇳 Vietnamese**: Ancestor veneration practices
- **🇰🇷 Korean**: Funeral rites & memorial services
- **✡️ Jewish**: Burial & shiva traditions
- **🇮🇷 Persian**: Iranian funeral customs
- **🇹🇭 Thai**: Buddhist funeral practices
- **🇰🇭 Cambodian**: Memorial traditions
- **🇷🇺 Russian**: Orthodox funeral customs
- **🇺🇦 Ukrainian**: Memorial services
- **🇯🇵 Japanese**: Buddhist & Shinto practices
- **🇸🇴 Somali**: Islamic funeral traditions
- **🇪🇹 Ethiopian**: Orthodox customs
- **🇨🇳 Chinese**: Ancestor worship & funeral rites
- **🇵🇱 Polish**: Catholic traditions
- **🇦🇲 Armenian**: Apostolic funeral customs
- **🇸🇻 Salvadoran**: Memorial traditions

### **Service Agents**
- **💰 Financial Services**: Payment plans & billing assistance
- **📋 Compliance**: Regulatory & documentation support
- **🚨 Emergency**: Crisis & urgent situation handling
- **🏢 Inventory**: Facilities & equipment management
- **💙 Grief Support**: Emotional support & counseling
- **⚖️ Regulatory**: Legal & regulatory compliance
- **🙏 Religious**: Interfaith religious services
- **🔍 Web Search**: Real-time information retrieval

### **MODERATOR System**
- **Central Routing**: Intelligent agent selection based on query analysis
- **Parallel Execution**: Multiple agents process queries simultaneously
- **Response Synthesis**: LLM-powered combination of agent insights
- **Collaboration Management**: 30s individual / 90s total timeouts

## 🧪 Testing & Quality

### **Backend Testing (72% Coverage)**
```bash
# Run full test suite
pytest

# Coverage analysis
pytest --cov=app --cov-report=html

# Voice Agent testing
python test_voice_agent.py           # Connection testing
python debug_voice_agent_events.py   # Real-time monitoring

# Frontend test simulation
curl -X POST http://localhost:8000/api/telephony/test/simulate-call
```

### **Frontend Testing**
```bash
# Unit & integration tests
npm test

# Coverage report
npm run test:coverage

# End-to-end testing
npm run test:integration
```

### **Test Statistics**
- **Overall Coverage**: 72% (improvement from 63%)
- **Test Success Rate**: 98.4% (1,360 of 1,382 tests passing)
- **Test Organization**: Comprehensive unit and integration suites
- **Voice Agent Tests**: Dedicated testing tools for WebSocket connections

## 📊 Monitoring & Analytics

### **System Metrics**
- **API Performance**: Response times, error rates, throughput
- **Voice Agent Performance**: Call success rates, latency metrics
- **Agent Analytics**: Usage patterns, collaboration success rates
- **Database Performance**: Query optimization, connection pooling
- **Real-time Monitoring**: Live call status, WebSocket connections

### **Usage Tracking**
- **Word-Based Billing**: STT/TTS word counts for accurate pricing
- **Call Duration**: Precise timing for telephony costs
- **Agent Usage**: Token consumption and collaboration metrics
- **Multi-tenant Analytics**: Organization-specific usage patterns

### **Logging & Alerting**
- **Structured Logging**: Correlation IDs for request tracing
- **Error Tracking**: Comprehensive error capture and alerting
- **Audit Trails**: Security and compliance logging
- **Performance Alerts**: Automated monitoring and notifications

## 🛡️ Security & Compliance

### **Authentication & Authorization**
- **JWT-based Authentication**: Secure token-based auth
- **Role Hierarchy**: `user` → `org_admin` → `admin` → `super_admin`
- **Multi-tenant Isolation**: Strict data segregation
- **API Rate Limiting**: DDoS protection and abuse prevention

### **Data Protection**
- **Encrypted Communications**: TLS/SSL for all API traffic
- **Secure Voice Streaming**: Encrypted WebSocket connections
- **PII Handling**: GDPR/CCPA compliant data processing
- **Input Sanitization**: XSS and injection attack prevention

### **Infrastructure Security**
- **Environment Variables**: Secure configuration management
- **Database Security**: Connection encryption, access controls
- **Service Isolation**: Containerized deployment with network isolation
- **Backup & Recovery**: Automated backup with encryption at rest

## 📦 Deployment & Operations

### **Production Deployment**
```bash
# Docker deployment
docker-compose up -d

# Environment configuration
USE_VOICE_AGENT=true
VOICE_AGENT_ROLLOUT_PERCENTAGE=100
DATABASE_URL=postgresql://user:pass@prod-db:5432/thanotopolis
DEEPGRAM_API_KEY=your_production_key
TWILIO_ACCOUNT_SID=your_production_sid
```

### **Infrastructure Requirements**
- **Database**: PostgreSQL 14+ with pgvector extension
- **Cache**: Redis for session management
- **Web Server**: Nginx + Gunicorn for production
- **WebSocket Support**: Load balancer with WebSocket support
- **SSL Certificates**: TLS termination for secure communications

### **Scalability Features**
- **Async Architecture**: FastAPI with async/await throughout
- **Connection Pooling**: Optimized database connections
- **WebSocket Scaling**: Horizontal scaling support
- **CDN Integration**: Static asset optimization
- **Monitoring**: Comprehensive observability stack

## 🤝 Contributing

### **Development Workflow**
1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** changes with comprehensive tests
4. **Run** test suite (`pytest` + `npm test`)
5. **Submit** pull request with detailed description

### **Code Standards**
- **Python**: PEP 8 compliance with Black formatting
- **TypeScript**: Strict typing with ESLint rules
- **Testing**: Minimum 70% coverage for new features
- **Documentation**: Comprehensive docstrings and comments
- **Security**: Security review for all auth/telephony changes

### **Voice Agent Development**
```bash
# Voice Agent testing environment
python test_voice_agent.py           # Test WebSocket connectivity
python debug_voice_agent_events.py   # Monitor real-time events

# Frontend testing
npm run dev                           # Start frontend
# Navigate to: /organizations/telephony/test
```

## 📖 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Comprehensive development guide
- **[Backend Guide](backend/CLAUDE.md)** - Backend architecture & Voice Agent details
- **[Frontend Guide](frontend/CLAUDE.md)** - Frontend architecture & UI components
- **[Agent Ownership Guide](backend/AGENT_OWNERSHIP_GUIDE.md)** - Multi-tenant agent system
- **[Barney Agent Summary](backend/BARNEY_AGENT_SUMMARY.md)** - Demo agent details

## 📄 License

This project is proprietary software owned by **Cyberiad.ai**. All rights reserved.

## 🚀 About Cyberiad.ai

**Cyberiad.ai** pioneers next-generation agentic AI frameworks that revolutionize how organizations deploy sophisticated AI assistants. Our platforms combine cutting-edge voice technology, multi-agent collaboration, and enterprise-grade scalability to deliver transformative customer experiences.

**Key Innovations:**
- **Voice Agent Technology**: First-to-market Deepgram Voice Agent integration
- **Multi-Agent Collaboration**: Consent-based specialist agent collaboration
- **Cultural Sensitivity**: 17 culturally-aware specialist agents
- **Enterprise Architecture**: Multi-tenant, scalable, secure platform

---

**Built with ❤️ by the Cyberiad.ai team**

*Transforming telephony with AI • Revolutionizing customer service • Pioneering the future of conversational AI*