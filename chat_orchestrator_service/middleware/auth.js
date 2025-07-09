const jwt = require('jsonwebtoken');
const logger = require('../utils/logger');
const { query } = require('../config/database');

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

async function authMiddleware(req, res, next) {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    
    if (!token) {
      return res.status(401).json({
        error: 'Access denied',
        message: 'No token provided'
      });
    }

    // Verify token
    const decoded = jwt.verify(token, JWT_SECRET);
    
    // Check if user exists in database
    const userResult = await query(
      'SELECT id, username, email, role FROM server.users WHERE id = $1 AND active = true',
      [decoded.userId]
    );
    
    if (userResult.rows.length === 0) {
      return res.status(401).json({
        error: 'Access denied',
        message: 'User not found or inactive'
      });
    }
    
    req.user = userResult.rows[0];
    next();
  } catch (error) {
    logger.error('Authentication error:', error);
    
    if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({
        error: 'Access denied',
        message: 'Invalid token'
      });
    }
    
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        error: 'Access denied',
        message: 'Token expired'
      });
    }
    
    return res.status(500).json({
      error: 'Internal server error',
      message: 'Authentication failed'
    });
  }
}

// Role-based access control middleware
function requireRole(roles) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        error: 'Access denied',
        message: 'User not authenticated'
      });
    }
    
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: 'Insufficient permissions'
      });
    }
    
    next();
  };
}

module.exports = authMiddleware;
module.exports.requireRole = requireRole;
