const OpenAI = require('openai');
const logger = require('../utils/logger');
const { query } = require('../config/database');

class OpenAIService {
  constructor() {
    this.client = null;
    this.initialized = false;
  }

  async initialize() {
    if (this.initialized) return;

    try {
      // Get API key from database
      const keyResult = await query(`
        SELECT api_key FROM server.ai_api_keys 
        WHERE provider = 'openai' AND active = true
        ORDER BY created_at DESC
        LIMIT 1
      `);

      if (keyResult.rows.length === 0) {
        throw new Error('No active OpenAI API key found');
      }

      this.client = new OpenAI({
        apiKey: keyResult.rows[0].api_key
      });

      this.initialized = true;
      logger.info('OpenAI service initialized');
    } catch (error) {
      logger.error('Failed to initialize OpenAI service:', error);
      throw error;
    }
  }

  async processMessage(message, context, phase) {
    await this.initialize();

    try {
      // Get phase-specific prompt template
      const promptTemplate = await this.getPromptTemplate(phase);
      
      // Build conversation context
      const messages = this.buildConversationContext(message, context, promptTemplate);

      // Make API call to OpenAI
      const response = await this.client.chat.completions.create({
        model: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview',
        messages: messages,
        max_tokens: 2000,
        temperature: 0.7,
        top_p: 1,
        frequency_penalty: 0,
        presence_penalty: 0
      });

      const aiResponse = response.choices[0].message.content;
      
      // Parse response for phase transitions and metadata
      const parsedResponse = this.parseAIResponse(aiResponse, phase);

      logger.info(`OpenAI response generated for phase: ${phase}`);

      return {
        content: parsedResponse.content,
        metadata: {
          provider: 'openai',
          model: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview',
          tokens_used: response.usage.total_tokens,
          phase: phase,
          ...parsedResponse.metadata
        },
        nextPhase: parsedResponse.nextPhase
      };
    } catch (error) {
      logger.error('OpenAI API error:', error);
      throw error;
    }
  }

  async getPromptTemplate(phase) {
    try {
      const templateResult = await query(`
        SELECT template_content, variables
        FROM legalbot.prompt_templates
        WHERE phase = $1 AND active = true
        ORDER BY version DESC
        LIMIT 1
      `, [phase || 'INFO_COLLECTION']);

      if (templateResult.rows.length === 0) {
        return this.getDefaultPromptTemplate(phase);
      }

      return templateResult.rows[0];
    } catch (error) {
      logger.error('Error getting prompt template:', error);
      return this.getDefaultPromptTemplate(phase);
    }
  }

  getDefaultPromptTemplate(phase) {
    const templates = {
      INFO_COLLECTION: {
        template_content: `You are a legal consultation assistant. Your role is to collect essential information from clients about their legal issues.

Current Phase: Information Collection

Instructions:
1. Ask relevant questions to understand the client's legal situation
2. Be empathetic and professional
3. Collect key details like dates, locations, parties involved
4. Guide the conversation toward case analysis once sufficient information is gathered
5. If you have enough information, respond with [NEXT_PHASE:CASE_ANALYSIS]

Previous conversation context will be provided. Use it to avoid repeating questions.`,
        variables: {}
      },
      CASE_ANALYSIS: {
        template_content: `You are a legal consultation assistant. Your role is to analyze the client's legal case and provide preliminary assessment.

Current Phase: Case Analysis

Instructions:
1. Analyze the information collected about the client's legal issue
2. Identify potential legal theories and claims
3. Assess the strength of the case
4. Highlight any important legal considerations
5. Prepare to transition to product recommendation if appropriate
6. If ready to recommend products/services, respond with [NEXT_PHASE:PRODUCT_RECOMMENDATION]

Provide clear, professional analysis while avoiding giving definitive legal advice.`,
        variables: {}
      },
      PRODUCT_RECOMMENDATION: {
        template_content: `You are a legal consultation assistant. Your role is to recommend appropriate legal products and services.

Current Phase: Product Recommendation

Instructions:
1. Based on the case analysis, recommend suitable legal services
2. Explain why each recommendation is appropriate for their situation
3. Provide estimated timelines and considerations
4. Prepare for sales conversion if the client shows interest
5. If client is ready to proceed, respond with [NEXT_PHASE:SALES_CONVERSION]

Be helpful and informative while being mindful of the client's needs and budget.`,
        variables: {}
      },
      SALES_CONVERSION: {
        template_content: `You are a legal consultation assistant. Your role is to guide the client through the sales conversion process.

Current Phase: Sales Conversion

Instructions:
1. Address any concerns about the recommended services
2. Provide clear next steps for engagement
3. Explain the process and what to expect
4. Offer to connect them with appropriate legal professionals
5. Ensure all questions are answered before proceeding

Be supportive and clear about the engagement process.`,
        variables: {}
      }
    };

    return templates[phase] || templates.INFO_COLLECTION;
  }

  buildConversationContext(message, context, promptTemplate) {
    const messages = [
      {
        role: 'system',
        content: promptTemplate.template_content
      }
    ];

    // Add conversation history
    context.forEach(msg => {
      messages.push({
        role: msg.sender_type === 'user' ? 'user' : 'assistant',
        content: msg.content
      });
    });

    // Add current message
    messages.push({
      role: 'user',
      content: message
    });

    return messages;
  }

  parseAIResponse(response, currentPhase) {
    const phaseTransitionRegex = /\[NEXT_PHASE:([A-Z_]+)\]/;
    const match = response.match(phaseTransitionRegex);
    
    let nextPhase = currentPhase;
    let content = response;
    
    if (match) {
      nextPhase = match[1];
      content = response.replace(phaseTransitionRegex, '').trim();
    }

    return {
      content,
      nextPhase,
      metadata: {
        phase_transition: match !== null,
        original_phase: currentPhase
      }
    };
  }
}

module.exports = new OpenAIService();
