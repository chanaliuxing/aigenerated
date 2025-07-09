#!/usr/bin/env node

/**
 * Database migration script for Legal Chatbot
 * This script handles database migrations and updates
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'legalbot',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'password',
};

async function runMigrations() {
  let client;
  
  try {
    console.log('🔄 Running database migrations...');
    
    // Connect to PostgreSQL
    client = new Client(dbConfig);
    await client.connect();
    console.log('✅ Connected to PostgreSQL');
    
    // Create migrations table if it doesn't exist
    await client.query(`
      CREATE TABLE IF NOT EXISTS migrations (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255) NOT NULL UNIQUE,
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // Get list of migration files
    const migrationsDir = path.join(__dirname, '../database/migrations');
    
    if (!fs.existsSync(migrationsDir)) {
      console.log('📁 No migrations directory found, creating...');
      fs.mkdirSync(migrationsDir, { recursive: true });
      
      // Create sample migration
      const sampleMigration = `-- Sample migration
-- This is a placeholder migration file
-- Add your migration SQL here

-- Example:
-- ALTER TABLE legalbot.conversations ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'medium';
`;
      
      fs.writeFileSync(
        path.join(migrationsDir, '001_sample_migration.sql'),
        sampleMigration
      );
      
      console.log('📝 Created sample migration file');
    }
    
    const migrationFiles = fs.readdirSync(migrationsDir)
      .filter(file => file.endsWith('.sql'))
      .sort();
    
    if (migrationFiles.length === 0) {
      console.log('📋 No migration files found');
      return;
    }
    
    // Get executed migrations
    const executedResult = await client.query('SELECT filename FROM migrations');
    const executedMigrations = executedResult.rows.map(row => row.filename);
    
    // Execute pending migrations
    let executedCount = 0;
    
    for (const file of migrationFiles) {
      if (executedMigrations.includes(file)) {
        console.log(`⏭️  Skipping ${file} (already executed)`);
        continue;
      }
      
      try {
        console.log(`🔄 Executing ${file}...`);
        
        const migrationPath = path.join(migrationsDir, file);
        const migrationSql = fs.readFileSync(migrationPath, 'utf8');
        
        // Execute migration in transaction
        await client.query('BEGIN');
        await client.query(migrationSql);
        await client.query('INSERT INTO migrations (filename) VALUES ($1)', [file]);
        await client.query('COMMIT');
        
        console.log(`✅ Successfully executed ${file}`);
        executedCount++;
        
      } catch (error) {
        await client.query('ROLLBACK');
        console.error(`❌ Failed to execute ${file}:`, error.message);
        throw error;
      }
    }
    
    if (executedCount === 0) {
      console.log('✅ All migrations are up to date');
    } else {
      console.log(`🎉 Successfully executed ${executedCount} migrations`);
    }
    
  } catch (error) {
    console.error('❌ Migration failed:', error.message);
    process.exit(1);
  } finally {
    if (client) {
      await client.end();
    }
  }
}

// Run migrations
runMigrations().catch(console.error);
