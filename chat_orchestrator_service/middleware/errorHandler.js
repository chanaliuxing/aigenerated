const logger = require('../utils/logger');

function errorHandler(error, req, res, next) {
  logger.error('Error occurred:', {
    error: error.message,
    stack: error.stack,
    url: req.url,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });

  // Default error response
  let status = 500;
  let message = 'Internal server error';
  let details = null;

  // Handle specific error types
  if (error.name === 'ValidationError') {
    status = 400;
    message = 'Validation error';
    details = error.details;
  } else if (error.name === 'UnauthorizedError') {
    status = 401;
    message = 'Unauthorized';
  } else if (error.name === 'ForbiddenError') {
    status = 403;
    message = 'Forbidden';
  } else if (error.name === 'NotFoundError') {
    status = 404;
    message = 'Not found';
  } else if (error.code === '23505') { // PostgreSQL unique violation
    status = 409;
    message = 'Conflict: Resource already exists';
  } else if (error.code === '23503') { // PostgreSQL foreign key violation
    status = 400;
    message = 'Invalid reference';
  } else if (error.code === '23502') { // PostgreSQL not null violation
    status = 400;
    message = 'Missing required field';
  }

  // Send error response
  const response = {
    error: message,
    status,
    timestamp: new Date().toISOString()
  };

  // Include error details in development
  if (process.env.NODE_ENV === 'development') {
    response.details = details || error.message;
    response.stack = error.stack;
  }

  res.status(status).json(response);
}

module.exports = errorHandler;
