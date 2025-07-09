const { Pool } = require('pg');
const logger = require('../utils/logger');

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'legalbot',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'password',
  max: 20, // Maximum number of connections in the pool
  idleTimeoutMillis: 30000, // Close idle connections after 30 seconds
  connectionTimeoutMillis: 2000, // Return error after 2 seconds if connection could not be established
  maxUses: 7500, // Close connection after 7500 uses
});

// Database connection function
async function connectDB() {
  try {
    const client = await pool.connect();
    logger.info('Database connected successfully');
    client.release();
    return true;
  } catch (error) {
    logger.error('Database connection error:', error);
    throw error;
  }
}

// Generic query function
async function query(text, params) {
  const start = Date.now();
  try {
    const result = await pool.query(text, params);
    const duration = Date.now() - start;
    logger.debug(`Query executed in ${duration}ms: ${text}`);
    return result;
  } catch (error) {
    logger.error('Database query error:', error);
    throw error;
  }
}

// Transaction wrapper
async function transaction(callback) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await callback(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

// Close all connections
async function closeDB() {
  await pool.end();
  logger.info('Database connections closed');
}

module.exports = {
  pool,
  connectDB,
  query,
  transaction,
  closeDB
};
