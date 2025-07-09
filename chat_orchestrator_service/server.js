const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const logger = require('./utils/logger');
const { connectDB } = require('./config/database');
const { connectRedis } = require('./config/redis');
const authMiddleware = require('./middleware/auth');
const errorHandler = require('./middleware/errorHandler');

// Route imports
const authRoutes = require('./routes/authRoutes');
const convoRoutes = require('./routes/convoRoutes');
const configRoutes = require('./routes/configRoutes');
const apiKeyRoutes = require('./routes/apiKeyRoutes');
const workflowRoutes = require('./routes/workflowRoutes');

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3001'],
    methods: ['GET', 'POST', 'PUT', 'DELETE']
  }
});

// Trust proxy for rate limiting
app.set('trust proxy', 1);

// Security middleware
app.use(helmet());
app.use(compression());

// CORS configuration
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3001'],
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use('/api/', limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: process.env.npm_package_version || '1.0.0'
  });
});

// API routes
app.use('/api/auth', authRoutes);
app.use('/api/conversations', authMiddleware, convoRoutes);
app.use('/api/config', authMiddleware, configRoutes);
app.use('/api/api-keys', authMiddleware, apiKeyRoutes);
app.use('/api/workflows', authMiddleware, workflowRoutes);

// WebSocket connection handling
io.use((socket, next) => {
  const token = socket.handshake.auth.token;
  if (!token) {
    return next(new Error('Authentication error'));
  }
  // Verify JWT token here
  next();
});

io.on('connection', (socket) => {
  logger.info(`Client connected: ${socket.id}`);
  
  socket.on('join-conversation', (conversationId) => {
    socket.join(`conversation:${conversationId}`);
    logger.info(`Client ${socket.id} joined conversation ${conversationId}`);
  });
  
  socket.on('send-message', async (data) => {
    try {
      // Process message and emit to conversation room
      const response = await processMessage(data);
      io.to(`conversation:${data.conversationId}`).emit('message-received', response);
    } catch (error) {
      logger.error('Error processing message:', error);
      socket.emit('error', { message: 'Failed to process message' });
    }
  });
  
  socket.on('disconnect', () => {
    logger.info(`Client disconnected: ${socket.id}`);
  });
});

// Error handling middleware
app.use(errorHandler);

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.originalUrl} not found`
  });
});

const PORT = process.env.PORT || 3000;

async function startServer() {
  try {
    // Connect to database
    await connectDB();
    logger.info('Database connected successfully');
    
    // Connect to Redis (optional)
    if (process.env.REDIS_URL) {
      await connectRedis();
      logger.info('Redis connected successfully');
    }
    
    // Start server
    server.listen(PORT, () => {
      logger.info(`Chat Orchestrator Service running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

// Function to process messages (placeholder)
async function processMessage(data) {
  // This would integrate with the Python consumer service
  // For now, return a mock response
  return {
    id: Date.now(),
    message: `Received: ${data.message}`,
    timestamp: new Date().toISOString(),
    conversationId: data.conversationId
  };
}

startServer();

module.exports = { app, io };
