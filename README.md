# Agent Framework - AI-Powered Multi-Tenant Communication Platform

A comprehensive AI platform designed for organizations requiring sophisticated voice and chat assistance. Built specifically for **Thanotopolis** (cemetery and funeral home services) but easily adaptable for other industries through configuration.

## 🎯 Core Features

### **🎙️ Advanced Voice Technology**
- **Deepgram Voice Agent Integration**: Unified STT+LLM+TTS with 90% latency reduction (<500ms response time)
- **Twilio Integration**: Professional telephony with call forwarding and analytics
- **Multi-language Support**: Automatic language detection and cultural adaptation
- **Real-time Collaboration**: Consent-based specialist agent consultation during calls

### **💬 Web Chat Application**
- **Multi-Agent Collaboration**: 20+ specialist agents for complex queries
- **Real-time Messaging**: WebSocket-based instant communication
- **Voice Integration**: Browser-based voice recording and playback
- **Conversation History**: Persistent chat sessions with search capabilities

### **📇 Comprehensive CRM System**
- **Contact Management**: Complete customer database with interaction tracking
- **Cemetery-Specific Fields**: Deceased info, service types, cultural preferences, financial tracking
- **Email Campaigns**: SendGrid integration with templated bulk messaging
- **CSV Import**: Bulk contact import with intelligent field mapping
- **Billing Integration**: Direct Stripe subscription and payment status linking

### **📅 Calendar & Scheduling System**
- **Multi-View Calendar**: Month, week, day views with event management
- **Advanced Attendee Management**: Internal users, CRM contacts, and external participants
- **CRM Integration**: Link events directly to contacts with full context
- **RSVP System**: Complete invitation and response tracking
- **Statistics Dashboard**: Event analytics and usage reports

### **🎯 Revolutionary Voice-to-CRM-to-Calendar Integration**
- **Automatic Data Extraction**: Extract customer information from voice conversations
- **Real-time CRM Creation**: Automatically create contacts during phone calls
- **Voice-Driven Scheduling**: Book appointments through natural conversation
- **Complete Workflow**: One call handles intake, contact creation, and scheduling

## 🏗️ Architecture

### **Technology Stack**
- **Backend**: FastAPI with async/await architecture
- **Frontend**: Next.js 19 with React 19 and TypeScript
- **Database**: PostgreSQL with pgvector extension
- **Authentication**: JWT-based with role hierarchy
- **Real-time**: WebSocket connections for chat and voice
- **Voice Processing**: Deepgram Voice Agent API
- **Email**: SendGrid integration
- **Payments**: Stripe billing system

### **AI Agent Network**
**17 Cultural Specialist Agents**:
- Mexican, Filipino, Vietnamese, Korean, Jewish, Persian, Thai, Cambodian, Russian, Ukrainian, Japanese, Somali, Ethiopian, Chinese, Polish, Armenian, Salvadoran

**Service Specialist Agents**:
- Financial Services, Compliance & Documentation, Emergency & Crisis, Inventory & Facilities, Grief Support, Regulatory, Religious Services, Web Search

**Central Orchestration**:
- MODERATOR agent for intelligent query routing and response synthesis
- Parallel processing with 30-second individual and 90-second total timeouts

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ with pgvector extension
- Required API keys (see configuration section below)

### **Backend Setup**
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (see Required API Keys section below)

# Setup database
alembic upgrade head

# Create admin user
python create_admin_user.py

# Start development server
python run.py
```

## 🔑 Required API Keys

The Agent Framework requires several API keys for different services. Configure these in your `backend/.env` file:

### **Core AI Services** (REQUIRED)
- **OpenAI API Key** (`OPENAI_API_KEY`)
  - **Purpose**: Core AI functionality for all agents and conversations
  - **Get it**: https://platform.openai.com/api-keys
  - **Critical**: ✅ System cannot function without this

### **Voice & Telephony** (REQUIRED if telephony enabled)
- **Twilio Account SID** (`TWILIO_ACCOUNT_SID`)
- **Twilio Auth Token** (`TWILIO_AUTH_TOKEN`) 
- **Twilio Phone Number** (`TWILIO_PHONE_NUMBER`)
  - **Purpose**: Phone call handling and SMS verification
  - **Get it**: https://www.twilio.com/console
  - **Critical**: ✅ Required for voice features

- **Deepgram API Key** (`DEEPGRAM_API_KEY`)
  - **Purpose**: Voice Agent API for STT+LLM+TTS processing
  - **Get it**: https://console.deepgram.com/
  - **Critical**: ✅ Required for voice processing

### **Email Services** (OPTIONAL but recommended)
- **SendGrid API Key** (`SENDGRID_API_KEY`)
  - **Purpose**: Email delivery for CRM campaigns and notifications
  - **Get it**: https://app.sendgrid.com/settings/api_keys
  - **Critical**: ⚠️ Optional - email features disabled without it

### **Billing & Payments** (OPTIONAL)
- **Stripe Secret Key** (`STRIPE_SECRET_KEY`)
- **Stripe Public Key** (`STRIPE_PUBLIC_KEY`)
  - **Purpose**: Payment processing and subscription billing
  - **Get it**: https://dashboard.stripe.com/apikeys
  - **Critical**: ⚠️ Optional - only needed for billing features

### **Legacy Services** (OPTIONAL)
- **ElevenLabs API Key** (`ELEVENLABS_API_KEY`)
  - **Purpose**: Legacy TTS service (may be deprecated)
  - **Get it**: https://elevenlabs.io/
  - **Critical**: ⚠️ Optional - system now uses Deepgram Voice Agent

### **Configuration Example**
```bash
# Core AI (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# Voice & Telephony (REQUIRED if telephony enabled)
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Email (OPTIONAL)
SENDGRID_API_KEY=your_sendgrid_api_key_here

# Billing (OPTIONAL)
STRIPE_SECRET_KEY=your_stripe_secret_key_here
STRIPE_PUBLIC_KEY=your_stripe_public_key_here

# Legacy (OPTIONAL)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### **Removed Services**
The following API keys were removed as they are not used in the current codebase:
- Microsoft Azure credentials (OneDrive integration - not implemented)
- Google API keys (Search integration - not implemented)
- Alternative AI providers (Anthropic, DeepSeek, Mistral, Cohere, Gemini, Together - not used)
- Soniox API (not used in current voice processing)

### **Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local with API URLs

# Start development server
npm run dev
```

### **Voice Agent Configuration**
```bash
# Enable Voice Agent in backend .env
USE_VOICE_AGENT=true
VOICE_AGENT_ROLLOUT_PERCENTAGE=100
VOICE_AGENT_LISTENING_MODEL=nova-3
VOICE_AGENT_THINKING_MODEL=gpt-4o-mini
VOICE_AGENT_SPEAKING_MODEL=aura-2-thalia-en
```

## 🎙️ How the Voice System Works

### **Telephony Flow**
1. **Customer calls** organization's existing number
2. **Call forwards** to platform's Twilio number
3. **Voice Agent answers** with personalized greeting
4. **Real-time conversation** with automatic data extraction
5. **Specialist consultation** if requested by customer
6. **Appointment booking** through natural conversation
7. **CRM contact created** with full conversation history
8. **Calendar event scheduled** and confirmed

### **Voice Agent Collaboration**
- **Smart Detection**: AI analyzes query complexity
- **User Consent**: "I can consult with my specialist team. This will take about 30 seconds."
- **Expert Routing**: Connects to cultural, financial, or service specialists
- **Seamless Integration**: Returns expert insights to voice conversation

### **Voice-to-CRM-to-Calendar Integration**
- **Real-time Extraction**: Customer info extracted during conversation
- **Automatic CRM Creation**: Contacts created with cemetery-specific fields
- **Live Scheduling**: Check availability and book appointments via voice
- **Complete Documentation**: Full conversation history linked to contacts and events

## 📇 CRM System Features

### **Contact Management**
- **Business Information**: Company details, contact persons, communication preferences
- **Cemetery-Specific Fields**: Deceased info, service types, cultural preferences
- **Financial Tracking**: Contract amounts, payments, balances (stored in cents)
- **Custom Fields**: Organization-specific dynamic fields
- **Interaction Timeline**: Complete history of calls, emails, meetings, notes

### **Email Campaigns**
- **Template System**: Jinja2-powered templates with variable substitution
- **Bulk Sending**: Personalized emails to multiple contacts
- **SendGrid Integration**: Professional delivery with tracking
- **Default Templates**: Welcome emails, follow-ups, invoice reminders

### **CSV Import**
- **Drag-and-Drop**: Intuitive field mapping interface
- **Smart Detection**: Automatic column recognition
- **Duplicate Handling**: Update existing or skip duplicates
- **Validation**: Real-time error detection with feedback

## 📅 Calendar System Features

### **Event Management**
- **Multi-View Calendar**: Interactive month, week, day views
- **Event Types**: Appointments, services, meetings, calls, reminders
- **CRM Integration**: Link events directly to contacts
- **All-Day Events**: Support for full-day events
- **Location Tracking**: Optional location field for events

### **Advanced Attendee Management**
- **Internal Users**: Multi-select team members from organization
- **CRM Contacts**: Searchable contact selection with command palette
- **External Attendees**: Email/name input for external participants
- **RSVP System**: Complete invitation and response tracking

### **Invitation System**
- **Invitation Tokens**: Unique secure RSVP links
- **Response Tracking**: Accepted, declined, tentative, no response
- **Email Integration**: Automated invitation sending
- **Public RSVP Pages**: Accessible response forms

## 🔧 Configuration & Customization

### **Framework Parameterization**
Easily adapt for different industries:

```bash
# Current (Funeral Home Industry)
FRAMEWORK_NAME=Thanotopolis
FRAMEWORK_DOMAIN=thanotopolis.com
FRAMEWORK_EMAIL=admin@thanotopolis.com
FRAMEWORK_DISPLAY_NAME=Thanotopolis

# Example (Medical Practice)
FRAMEWORK_NAME=MedAssist
FRAMEWORK_DOMAIN=medassist.com
FRAMEWORK_EMAIL=admin@medassist.com
FRAMEWORK_DISPLAY_NAME=MedAssist
```

### **Voice Agent Customization**
Organizations can customize their voice agent through Admin UI:
- **Greeting Style**: Custom welcome messages and tone
- **Business Context**: Specific services, pricing, policies
- **Personality Traits**: Professional, friendly, empathetic
- **Cultural Considerations**: Language preferences, customs
- **Knowledge Base**: Organization-specific information

## 🛡️ Security & Compliance

### **Authentication & Authorization**
- **JWT-based Authentication**: Secure token-based auth with refresh rotation
- **Role Hierarchy**: `user` → `org_admin` → `admin` → `super_admin`
- **Multi-tenant Isolation**: Strict data segregation by organization
- **API Rate Limiting**: DDoS protection and abuse prevention

### **Data Protection**
- **Encrypted Communications**: TLS/SSL for all API traffic
- **Secure Voice Streaming**: Encrypted WebSocket connections
- **PII Handling**: GDPR/CCPA compliant data processing
- **Input Sanitization**: XSS and injection attack prevention

## 📊 API Architecture

### **Core Endpoints**
- **`/api/auth/*`** - Authentication & user management
- **`/api/conversations/*`** - Chat & message handling
- **`/api/agents/*`** - Agent discovery & configuration
- **`/api/telephony/*`** - Phone system integration
- **`/api/crm/*`** - Contact management & CRM operations
- **`/api/calendar/*`** - Calendar & event management
- **`/api/billing/*`** - Usage tracking & payments
- **`/api/organizations/*`** - Multi-tenant management

### **Real-time WebSocket Endpoints**
- **`/api/ws/conversation/{id}`** - Chat conversations
- **`/api/ws/telephony/voice-agent/stream`** - Voice Agent streaming
- **`/api/ws/voice/{conversation_id}`** - Voice chat

## 🧪 Testing & Quality

### **Test Coverage**
- **Backend**: 72% coverage with comprehensive unit and integration tests
- **Frontend**: Jest with React Testing Library
- **Voice Agent**: Dedicated WebSocket connectivity testing
- **Test Success Rate**: 98.4% (1,360 of 1,382 tests passing)

### **Testing Commands**
```bash
# Backend testing
pytest --cov=app --cov-report=html

# Frontend testing
npm test

# Voice Agent testing
python test_voice_agent.py
python debug_voice_agent_events.py
```

## 📦 Deployment

### **Production Environment**
```bash
# Environment variables
USE_VOICE_AGENT=true
VOICE_AGENT_ROLLOUT_PERCENTAGE=100
DATABASE_URL=postgresql://user:pass@prod-db:5432/agent_framework
DEEPGRAM_API_KEY=your_production_key
TWILIO_ACCOUNT_SID=your_production_sid
SENDGRID_API_KEY=your_sendgrid_key
STRIPE_SECRET_KEY=your_stripe_key
```

### **Docker Deployment**
```bash
docker-compose up -d
```

### **Infrastructure Requirements**
- PostgreSQL 14+ with pgvector extension
- Nginx + Gunicorn for production
- Load balancer with WebSocket support
- SSL certificates for secure communications

## 🤝 Contributing

### **Development Workflow**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes with comprehensive tests
4. Run test suite (`pytest` + `npm test`)
5. Submit pull request with detailed description

### **Code Standards**
- **Python**: PEP 8 compliance with Black formatting
- **TypeScript**: Strict typing with ESLint rules
- **Testing**: Minimum 70% coverage for new features
- **Documentation**: Comprehensive docstrings and comments

## 📖 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Comprehensive development guide
- **[Backend Guide](backend/CLAUDE.md)** - Backend architecture & Voice Agent details
- **[Frontend Guide](frontend/CLAUDE.md)** - Frontend architecture & UI components

## 📄 License

This project is proprietary software owned by **Cyberiad.ai**. All rights reserved.

## 🚀 About Cyberiad.ai

**Cyberiad.ai** develops advanced agentic AI frameworks that enable organizations to deploy sophisticated AI assistants across telephony and web chat channels. Our platforms combine voice technology, multi-agent collaboration, and enterprise-grade scalability to deliver enhanced customer experiences.

**Key Innovations:**
- **Voice Agent Technology**: Deepgram integration with revolutionary automation
- **Multi-Agent Collaboration**: Consent-based specialist agent consultation
- **Cultural Sensitivity**: 17 culturally-aware specialist agents
- **Voice-to-CRM-to-Calendar**: Revolutionary conversation automation system
- **Enterprise Architecture**: Multi-tenant, scalable, secure platform

---

**Built with ❤️ by the Cyberiad.ai team**

*Advanced telephony and web chat AI • Enhanced customer service • Intelligent conversational AI • Revolutionary voice automation*