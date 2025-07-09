# Legal Chatbot Project - Installation Guide

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- PostgreSQL 13+
- Redis (optional but recommended)

### 1. Clone and Setup
```bash
# Clone the repository (or extract to folder)
cd legal-chatbot

# Copy environment variables
cp .env.example .env

# Edit .env file with your configuration
# Update database credentials, API keys, etc.
```

### 2. Install Dependencies
```bash
# Install Node.js dependencies
npm run install:all

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Create PostgreSQL database
createdb legalbot

# Run database setup script
npm run db:setup

# Run migrations (if any)
npm run db:migrate
```

### 4. Start Services
```bash
# Start all services in development mode
npm run dev

# Or start individual services:
npm run dev:orchestrator  # Chat Orchestrator (port 3000)
npm run dev:admin        # Admin Panel (port 3001)
npm run dev:webserver    # Web Server (port 5000)
npm run dev:consumer     # Python Consumer
```

### 5. Access the Application
- **Admin Panel**: http://localhost:3001
- **API Documentation**: http://localhost:3000/health
- **Web Interface**: http://localhost:5000

## 📋 Service Configuration

### Chat Orchestrator Service
```bash
cd chat_orchestrator_service
npm install
npm run dev
```

### Admin Panel
```bash
cd my-admin-panel
npm install
npm run dev
```

### Python Consumer
```bash
cd py_consumer
python start_consumer.py
```

### WeChat Automation (Optional)
```bash
cd wechat_automation_service
python main.py
```

## 🔧 Configuration

### Environment Variables
Key variables to configure in `.env`:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=legalbot
DB_USER=postgres
DB_PASSWORD=your_password

# AI Providers
OPENAI_API_KEY=your_openai_key
DEEPSEEK_API_KEY=your_deepseek_key
DEFAULT_AI_PROVIDER=openai

# Authentication
JWT_SECRET=your_jwt_secret

# Redis (optional)
REDIS_URL=redis://localhost:6379
```

### API Keys Setup
1. Get OpenAI API key from https://platform.openai.com/
2. Get DeepSeek API key from https://platform.deepseek.com/
3. Add keys to `.env` file or manage through admin panel

## 🐳 Docker Deployment

### Using Docker Compose
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Individual Service Deployment
```bash
# Build specific service
docker-compose build chat-orchestrator

# Start specific service
docker-compose up chat-orchestrator
```

## 📊 Default Accounts

### Admin User
- **Username**: admin
- **Password**: admin123
- **Email**: admin@legalbot.com

### Database Schemas
- **legalbot**: Main application data
- **server**: Infrastructure data
- **client**: CRM data

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check PostgreSQL is running
   pg_ctl status
   
   # Verify database exists
   psql -l | grep legalbot
   ```

2. **Python Dependencies**
   ```bash
   # Install missing packages
   pip install asyncpg psycopg2-binary
   pip install openai sentence-transformers
   ```

3. **Node.js Issues**
   ```bash
   # Clear npm cache
   npm cache clean --force
   
   # Reinstall dependencies
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Port Conflicts**
   ```bash
   # Check what's using the port
   netstat -tulpn | grep :3000
   
   # Kill process if needed
   kill -9 <PID>
   ```

## 📚 API Documentation

### Authentication
```bash
# Login
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Conversations
```bash
# Get conversations
curl -X GET http://localhost:3000/api/conversations \
  -H "Authorization: Bearer <token>"
```

### Health Check
```bash
# Check service health
curl http://localhost:3000/health
```

## 🚀 Production Deployment

### Requirements
- Reverse proxy (Nginx)
- SSL certificates
- Environment-specific configuration
- Database backups
- Log rotation

### Security Checklist
- [ ] Change default passwords
- [ ] Set strong JWT secret
- [ ] Configure HTTPS
- [ ] Set up firewall rules
- [ ] Enable database encryption
- [ ] Configure rate limiting

## 🔄 Updates and Maintenance

### Database Migrations
```bash
# Run new migrations
npm run db:migrate

# Check migration status
npm run db:status
```

### Backup and Restore
```bash
# Backup database
pg_dump legalbot > backup.sql

# Restore database
psql legalbot < backup.sql
```

### Log Management
```bash
# View logs
tail -f logs/combined.log

# Rotate logs
logrotate /etc/logrotate.d/legalbot
```

## 🆘 Support

### Getting Help
1. Check the logs in `logs/` directory
2. Review the troubleshooting section
3. Check database connectivity
4. Verify environment variables

### Development Mode
```bash
# Start with debug logging
DEBUG=true npm run dev

# Run with hot reload
npm run dev:watch
```

### Production Mode
```bash
# Build for production
npm run build

# Start production server
npm start
```

## 📈 Monitoring

### Health Checks
- `/health` - Service health
- `/api/health` - API health
- Database connection status

### Metrics
- Active conversations
- Response times
- Error rates
- AI provider usage

This installation guide provides comprehensive setup instructions for the Legal Chatbot project. Follow the steps in order for the best experience.
