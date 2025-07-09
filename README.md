# Legal Chatbot Project - Complete Architecture

## 🏗️ Project Overview

This is a **sophisticated legal consultation chatbot system** with advanced automation capabilities. The system combines AI-powered legal advice with WeChat automation for client interactions, built on a **microservices architecture** with multi-round conversation flows.

## � Core Features

### 🤖 AI-Powered Legal Consultation
- **Multi-round conversation flows** with phase management
- **OpenAI GPT + DeepSeek integration** for diverse AI capabilities
- **RAG (Retrieval-Augmented Generation)** for legal document search
- **Intelligent phase transitions** (Info Collection → Case Analysis → Product Recommendation → Sales Conversion)

### 📱 Multi-Platform Support
- **WeChat automation** for client interactions
- **Modern web interface** for public access
- **Admin panel** for management and configuration
- **Real-time WebSocket** communication

### 🔧 Advanced Automation
- **Desktop automation** for WeChat interactions
- **Workflow engine** with visual editor
- **Automated client management** and CRM integration
- **Intelligent task scheduling**

## 📂 Project Structure

```
legal-chatbot/
├── 🎛️ chat_orchestrator_service/    # Central API server (Node.js)
│   ├── server.js                    # Main server entry point
│   ├── routes/                      # API endpoints
│   ├── middleware/                  # Authentication & validation
│   ├── services/                    # AI provider integrations
│   └── config/                      # Database & Redis config
│
├── 🤖 py_consumer/                  # Python LLM processor
│   ├── start_consumer.py           # Main consumer entry point
│   ├── handlers/                   # Request handlers
│   ├── logic/                      # Business logic
│   └── utils/                      # Utilities & config
│
├── 🖥️ my-admin-panel/              # Next.js admin interface
│   ├── src/app/                    # App router pages
│   ├── src/components/             # React components
│   └── src/lib/                    # Utilities & API client
│
├── 📱 wechat_automation_service/    # Desktop automation
│   ├── main.py                     # Service entry point
│   ├── engine.py                   # Workflow engine
│   ├── basic_actions.py            # 2600+ automation actions
│   └── gui/                        # System tray interface
│
├── 🕸️ webserver/                   # Flask web application
│   ├── run.py                      # Flask app entry point
│   ├── models/                     # Database models
│   └── routes/                     # Web routes
│
├── 🧠 rag/                         # RAG system
│   ├── rag_deepseek.py             # DeepSeek RAG integration
│   ├── step2_create_knowledge_base.py # Knowledge base creation
│   └── data/                       # Legal documents
│
├── 🎨 chatgpt_microservice/        # Dedicated ChatGPT service
│   └── main.py                     # Microservice entry point
│
├── 🔌 nodeRed/                     # Node-RED integration
│   ├── index.js                    # Node-RED nodes
│   └── generator.py                # Node generator
│
├── 🗄️ database/                    # Database schemas
│   ├── schema.sql                  # Complete database schema
│   └── migrations/                 # Database migrations
│
├── 🐳 docker/                      # Docker configuration
│   └── docker-compose.yml          # Multi-service deployment
│
└── 📜 scripts/                     # Setup & utility scripts
    ├── setup-database.js           # Database initialization
    └── migrate-database.js         # Migration runner
```

## 🏛️ Database Architecture

### 📊 Multi-Schema Design
```sql
-- Core Schemas
├── legalbot.*     # Main application data
│   ├── conversations      # Chat sessions
│   ├── messages          # Individual messages
│   ├── contacts          # Client information
│   ├── phases            # Conversation phases
│   ├── prompt_templates  # AI prompt templates
│   └── knowledge_base    # RAG documents
│
├── server.*       # Infrastructure data
│   ├── users             # System users
│   ├── machines          # Automation machines
│   ├── workflows         # Automation workflows
│   └── ai_api_keys       # AI provider keys
│
└── client.*       # CRM data
    ├── users             # Client information
    ├── wechat_chats      # WeChat history
    └── cases             # Legal cases
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- PostgreSQL 13+
- Redis (optional)

### Installation
```bash
# Install dependencies
npm run install:all

# Setup database
npm run db:setup

# Start all services
npm run dev
```

## 🔧 Services

### 1. Chat Orchestrator Service (Port 3000)
- **Central command center** for all interactions
- **WebSocket gateway** for real-time communication
- **JWT authentication** middleware
- **Multi-AI provider** integration (OpenAI, DeepSeek)

### 2. Python Consumer Service
- **Async message processing** with workflow engine
- **Multi-round conversation** management
- **Slot filling** and data extraction
- **Dynamic prompt** generation

### 3. Admin Panel (Port 3001)
- **Next.js 14** with App Router
- **Real-time dashboard** with metrics
- **Prompt template** management
- **Workflow configuration** interface

### 4. WeChat Automation Service
- **Desktop automation** with 2600+ actions
- **Visual workflow editor** with drag-and-drop
- **System tray** background operation
- **Real-time task** execution

### 5. RAG System
- **FAISS vector search** for document retrieval
- **Sentence transformer** embeddings
- **Legal document** knowledge base
- **Context-aware** response generation

## 🔐 Security Features

### 🛡️ Authentication & Authorization
- **JWT tokens** with expiration
- **Role-based access** control (admin, user, operator)
- **API key management** for AI providers
- **Session management** with timeout

### 🔒 Data Protection
- **Password hashing** with bcrypt
- **Database encryption** support
- **Rate limiting** for API endpoints
- **CORS configuration** for web security

## 🚀 Deployment Options

### 🐳 Docker Deployment
```bash
# Single command deployment
docker-compose up -d

# Services included:
# - PostgreSQL with schemas
# - Redis cache
# - All microservices
# - Nginx reverse proxy
```

### ☁️ Cloud Deployment
- **Kubernetes** manifests included
- **Environment-based** configuration
- **Auto-scaling** capabilities
- **Load balancing** support

## 📈 Monitoring & Analytics

### � Built-in Metrics
- **Conversation analytics** and success rates
- **Response time** monitoring
- **AI provider usage** tracking
- **Error rate** and system health

### � Logging System
- **Structured logging** with Winston
- **Log rotation** and archival
- **Error tracking** and alerting
- **Performance monitoring**

## 🎯 Getting Started

### ⚡ Quick Start
```bash
# 1. Install dependencies
npm run install:all

# 2. Setup database
npm run db:setup

# 3. Configure environment
cp .env.example .env

# 4. Start all services
npm run dev
```

### 🎯 First Steps
1. **Access Admin Panel**: http://localhost:3001
2. **Login**: admin / admin123
3. **Configure AI Keys**: Settings → API Keys
4. **Test Conversation**: Create test conversation
5. **Monitor Dashboard**: View real-time metrics

## � Support & Documentation

For detailed setup instructions, see [INSTALLATION.md](INSTALLATION.md)
For API documentation, visit the running service at `/api/docs`
For troubleshooting, check the logs in the `logs/` directory

**Happy Coding! 🚀**
