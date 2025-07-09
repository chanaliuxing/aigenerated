const express = require('express');
const Joi = require('joi');
const router = express.Router();
const { query, transaction } = require('../config/database');
const logger = require('../utils/logger');
const openai = require('../services/openaiService');
const deepseek = require('../services/deepseekService');

// Validation schemas
const messageSchema = Joi.object({
  message: Joi.string().required(),
  conversationId: Joi.string().uuid().optional(),
  phase: Joi.string().optional(),
  metadata: Joi.object().optional()
});

const conversationSchema = Joi.object({
  contactId: Joi.string().uuid().required(),
  subject: Joi.string().max(255).optional(),
  metadata: Joi.object().optional()
});

// Get all conversations for a user
router.get('/', async (req, res, next) => {
  try {
    const { page = 1, limit = 20, status, phase } = req.query;
    const offset = (page - 1) * limit;

    let whereClause = 'WHERE c.user_id = $1';
    const params = [req.user.id];

    if (status) {
      whereClause += ' AND c.status = $' + (params.length + 1);
      params.push(status);
    }

    if (phase) {
      whereClause += ' AND c.current_phase = $' + (params.length + 1);
      params.push(phase);
    }

    const conversationsResult = await query(`
      SELECT 
        c.id,
        c.contact_id,
        c.subject,
        c.status,
        c.current_phase,
        c.created_at,
        c.updated_at,
        ct.name as contact_name,
        ct.email as contact_email,
        COUNT(m.id) as message_count,
        MAX(m.created_at) as last_message_at
      FROM legalbot.conversations c
      LEFT JOIN legalbot.contacts ct ON c.contact_id = ct.id
      LEFT JOIN legalbot.messages m ON c.id = m.conversation_id
      ${whereClause}
      GROUP BY c.id, ct.name, ct.email
      ORDER BY c.updated_at DESC
      LIMIT $${params.length + 1} OFFSET $${params.length + 2}
    `, [...params, limit, offset]);

    // Get total count
    const countResult = await query(`
      SELECT COUNT(*) as total
      FROM legalbot.conversations c
      ${whereClause}
    `, params);

    res.json({
      success: true,
      conversations: conversationsResult.rows,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total: parseInt(countResult.rows[0].total),
        pages: Math.ceil(countResult.rows[0].total / limit)
      }
    });
  } catch (error) {
    next(error);
  }
});

// Get a specific conversation
router.get('/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    const { includeMessages = 'true' } = req.query;

    // Get conversation details
    const conversationResult = await query(`
      SELECT 
        c.*,
        ct.name as contact_name,
        ct.email as contact_email,
        ct.phone as contact_phone
      FROM legalbot.conversations c
      LEFT JOIN legalbot.contacts ct ON c.contact_id = ct.id
      WHERE c.id = $1 AND c.user_id = $2
    `, [id, req.user.id]);

    if (conversationResult.rows.length === 0) {
      return res.status(404).json({
        error: 'Conversation not found'
      });
    }

    const conversation = conversationResult.rows[0];

    // Get messages if requested
    if (includeMessages === 'true') {
      const messagesResult = await query(`
        SELECT *
        FROM legalbot.messages
        WHERE conversation_id = $1
        ORDER BY created_at ASC
      `, [id]);

      conversation.messages = messagesResult.rows;
    }

    res.json({
      success: true,
      conversation
    });
  } catch (error) {
    next(error);
  }
});

// Create a new conversation
router.post('/', async (req, res, next) => {
  try {
    const { error, value } = conversationSchema.validate(req.body);
    if (error) {
      return res.status(400).json({
        error: 'Validation error',
        details: error.details
      });
    }

    const { contactId, subject, metadata } = value;

    // Check if contact exists
    const contactResult = await query(
      'SELECT id FROM legalbot.contacts WHERE id = $1',
      [contactId]
    );

    if (contactResult.rows.length === 0) {
      return res.status(400).json({
        error: 'Contact not found'
      });
    }

    const newConversation = await query(`
      INSERT INTO legalbot.conversations (contact_id, user_id, subject, metadata)
      VALUES ($1, $2, $3, $4)
      RETURNING *
    `, [contactId, req.user.id, subject, metadata]);

    logger.info(`New conversation created: ${newConversation.rows[0].id}`);

    res.status(201).json({
      success: true,
      conversation: newConversation.rows[0]
    });
  } catch (error) {
    next(error);
  }
});

// Send a message in a conversation
router.post('/:id/messages', async (req, res, next) => {
  try {
    const { id: conversationId } = req.params;
    const { error, value } = messageSchema.validate(req.body);
    
    if (error) {
      return res.status(400).json({
        error: 'Validation error',
        details: error.details
      });
    }

    const { message, phase, metadata } = value;

    // Verify conversation exists and user has access
    const conversationResult = await query(`
      SELECT * FROM legalbot.conversations 
      WHERE id = $1 AND user_id = $2
    `, [conversationId, req.user.id]);

    if (conversationResult.rows.length === 0) {
      return res.status(404).json({
        error: 'Conversation not found'
      });
    }

    const conversation = conversationResult.rows[0];

    // Process message with AI
    const aiResponse = await processMessageWithAI(message, conversation, phase);

    // Save messages in transaction
    const result = await transaction(async (client) => {
      // Save user message
      const userMessage = await client.query(`
        INSERT INTO legalbot.messages (conversation_id, sender_type, content, metadata)
        VALUES ($1, 'user', $2, $3)
        RETURNING *
      `, [conversationId, message, metadata]);

      // Save AI response
      const aiMessage = await client.query(`
        INSERT INTO legalbot.messages (conversation_id, sender_type, content, metadata)
        VALUES ($1, 'assistant', $2, $3)
        RETURNING *
      `, [conversationId, aiResponse.content, aiResponse.metadata]);

      // Update conversation phase if changed
      if (aiResponse.nextPhase && aiResponse.nextPhase !== conversation.current_phase) {
        await client.query(`
          UPDATE legalbot.conversations 
          SET current_phase = $1, updated_at = CURRENT_TIMESTAMP
          WHERE id = $2
        `, [aiResponse.nextPhase, conversationId]);
      }

      return {
        userMessage: userMessage.rows[0],
        aiMessage: aiMessage.rows[0]
      };
    });

    logger.info(`Message processed for conversation: ${conversationId}`);

    res.json({
      success: true,
      userMessage: result.userMessage,
      aiMessage: result.aiMessage,
      nextPhase: aiResponse.nextPhase
    });
  } catch (error) {
    next(error);
  }
});

// Update conversation status
router.patch('/:id/status', async (req, res, next) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    if (!['active', 'closed', 'archived'].includes(status)) {
      return res.status(400).json({
        error: 'Invalid status',
        message: 'Status must be one of: active, closed, archived'
      });
    }

    const result = await query(`
      UPDATE legalbot.conversations 
      SET status = $1, updated_at = CURRENT_TIMESTAMP
      WHERE id = $2 AND user_id = $3
      RETURNING *
    `, [status, id, req.user.id]);

    if (result.rows.length === 0) {
      return res.status(404).json({
        error: 'Conversation not found'
      });
    }

    res.json({
      success: true,
      conversation: result.rows[0]
    });
  } catch (error) {
    next(error);
  }
});

// Process message with AI
async function processMessageWithAI(message, conversation, phase) {
  try {
    // Get conversation context
    const contextResult = await query(`
      SELECT content, sender_type, created_at
      FROM legalbot.messages
      WHERE conversation_id = $1
      ORDER BY created_at DESC
      LIMIT 10
    `, [conversation.id]);

    const context = contextResult.rows.reverse();

    // Determine AI provider based on configuration
    const aiProvider = process.env.DEFAULT_AI_PROVIDER || 'openai';
    
    let aiResponse;
    if (aiProvider === 'deepseek') {
      aiResponse = await deepseek.processMessage(message, context, phase);
    } else {
      aiResponse = await openai.processMessage(message, context, phase);
    }

    return aiResponse;
  } catch (error) {
    logger.error('AI processing error:', error);
    return {
      content: 'I apologize, but I encountered an error processing your message. Please try again.',
      metadata: { error: true, provider: process.env.DEFAULT_AI_PROVIDER },
      nextPhase: phase
    };
  }
}

module.exports = router;
