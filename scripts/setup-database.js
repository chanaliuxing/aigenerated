#!/usr/bin/env node

/**
 * Database setup script for Legal Chatbot
 * This script creates the database schema and initial data
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

async function setupDatabase() {
  let client;
  
  try {
    console.log('🔧 Setting up Legal Chatbot database...');
    
    // Connect to PostgreSQL
    client = new Client(dbConfig);
    await client.connect();
    console.log('✅ Connected to PostgreSQL');
    
    // Read and execute schema file
    const schemaPath = path.join(__dirname, '../database/schema.sql');
    if (fs.existsSync(schemaPath)) {
      const schema = fs.readFileSync(schemaPath, 'utf8');
      await client.query(schema);
      console.log('✅ Database schema created successfully');
    } else {
      console.error('❌ Schema file not found:', schemaPath);
      process.exit(1);
    }
    
    // Check if tables were created
    const tablesResult = await client.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema IN ('legalbot', 'server', 'client')
      ORDER BY table_schema, table_name
    `);
    
    console.log('📋 Created tables:');
    tablesResult.rows.forEach(row => {
      console.log(`   - ${row.table_name}`);
    });
    
    // Verify seed data
    const userCount = await client.query('SELECT COUNT(*) FROM server.users');
    const phaseCount = await client.query('SELECT COUNT(*) FROM legalbot.phases');
    const templateCount = await client.query('SELECT COUNT(*) FROM legalbot.prompt_templates');
    
    console.log('\n📊 Initial data:');
    console.log(`   - Users: ${userCount.rows[0].count}`);
    console.log(`   - Phases: ${phaseCount.rows[0].count}`);
    console.log(`   - Prompt Templates: ${templateCount.rows[0].count}`);
    
    console.log('\n🎉 Database setup completed successfully!');
    console.log('\n📝 Default admin credentials:');
    console.log('   Username: admin');
    console.log('   Password: admin123');
    console.log('   Email: admin@legalbot.com');
    
  } catch (error) {
    console.error('❌ Database setup failed:', error.message);
    process.exit(1);
  } finally {
    if (client) {
      await client.end();
    }
  }
}

// Run the setup
setupDatabase().catch(console.error);
