const redis = require('redis');
const logger = require('../utils/logger');

let redisClient = null;

async function connectRedis() {
  if (!process.env.REDIS_URL) {
    logger.warn('Redis URL not provided, skipping Redis connection');
    return null;
  }

  try {
    redisClient = redis.createClient({
      url: process.env.REDIS_URL,
      retry_strategy: (options) => {
        if (options.error && options.error.code === 'ECONNREFUSED') {
          logger.error('Redis server refused connection');
          return new Error('Redis server refused connection');
        }
        if (options.total_retry_time > 1000 * 60 * 60) {
          logger.error('Redis retry time exhausted');
          return new Error('Redis retry time exhausted');
        }
        if (options.attempt > 10) {
          logger.error('Redis connection attempts exhausted');
          return undefined;
        }
        // Reconnect after
        return Math.min(options.attempt * 100, 3000);
      }
    });

    redisClient.on('error', (err) => {
      logger.error('Redis error:', err);
    });

    redisClient.on('connect', () => {
      logger.info('Redis connected successfully');
    });

    redisClient.on('ready', () => {
      logger.info('Redis ready for commands');
    });

    redisClient.on('reconnecting', () => {
      logger.info('Redis reconnecting...');
    });

    await redisClient.connect();
    return redisClient;
  } catch (error) {
    logger.error('Redis connection error:', error);
    throw error;
  }
}

// Cache operations
async function setCache(key, value, expireInSeconds = 3600) {
  if (!redisClient) return null;
  
  try {
    await redisClient.setEx(key, expireInSeconds, JSON.stringify(value));
    return true;
  } catch (error) {
    logger.error('Redis set error:', error);
    return false;
  }
}

async function getCache(key) {
  if (!redisClient) return null;
  
  try {
    const value = await redisClient.get(key);
    return value ? JSON.parse(value) : null;
  } catch (error) {
    logger.error('Redis get error:', error);
    return null;
  }
}

async function deleteCache(key) {
  if (!redisClient) return null;
  
  try {
    await redisClient.del(key);
    return true;
  } catch (error) {
    logger.error('Redis delete error:', error);
    return false;
  }
}

async function flushCache() {
  if (!redisClient) return null;
  
  try {
    await redisClient.flushAll();
    return true;
  } catch (error) {
    logger.error('Redis flush error:', error);
    return false;
  }
}

module.exports = {
  connectRedis,
  setCache,
  getCache,
  deleteCache,
  flushCache,
  redisClient: () => redisClient
};
