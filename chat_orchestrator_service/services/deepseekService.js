const axios = require('axios');
const logger = require('../utils/logger');
const { query } = require('../config/database');

class DeepSeekService {
  constructor() {
    this.apiKey = null;
    this.baseURL = 'https://api.deepseek.com/v1';
    this.initialized = false;
  }

  async initialize() {
    if (this.initialized) return;

    try {
      // Get API key from database
      const keyResult = await query(`
        SELECT api_key FROM server.ai_api_keys 
        WHERE provider = 'deepseek' AND active = true
        ORDER BY created_at DESC
        LIMIT 1
      `);

      if (keyResult.rows.length === 0) {
        throw new Error('No active DeepSeek API key found');
      }

      this.apiKey = keyResult.rows[0].api_key;
      this.initialized = true;
      logger.info('DeepSeek service initialized');
    } catch (error) {
      logger.error('Failed to initialize DeepSeek service:', error);
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

      // Make API call to DeepSeek
      const response = await axios.post(
        `${this.baseURL}/chat/completions`,
        {
          model: 'deepseek-chat',
          messages: messages,
          max_tokens: 2000,
          temperature: 0.7,
          stream: false
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const aiResponse = response.data.choices[0].message.content;
      
      // Parse response for phase transitions and metadata
      const parsedResponse = this.parseAIResponse(aiResponse, phase);

      logger.info(`DeepSeek response generated for phase: ${phase}`);

      return {
        content: parsedResponse.content,
        metadata: {
          provider: 'deepseek',
          model: 'deepseek-chat',
          tokens_used: response.data.usage.total_tokens,
          phase: phase,
          ...parsedResponse.metadata
        },
        nextPhase: parsedResponse.nextPhase
      };
    } catch (error) {
      logger.error('DeepSeek API error:', error);
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
        template_content: `你是一个法律咨询助手。你的角色是收集客户法律问题的基本信息。

当前阶段：信息收集

指令：
1. 询问相关问题以了解客户的法律情况
2. 保持同理心和专业性
3. 收集关键细节，如日期、地点、涉及的当事人
4. 收集到足够信息后，引导对话进入案例分析阶段
5. 如果你有足够的信息，请回复 [NEXT_PHASE:CASE_ANALYSIS]

将提供之前的对话上下文。使用它来避免重复问题。`,
        variables: {}
      },
      CASE_ANALYSIS: {
        template_content: `你是一个法律咨询助手。你的角色是分析客户的法律案例并提供初步评估。

当前阶段：案例分析

指令：
1. 分析收集到的客户法律问题信息
2. 识别潜在的法律理论和诉求
3. 评估案件的强度
4. 强调任何重要的法律考虑因素
5. 准备过渡到产品推荐阶段（如果适当）
6. 如果准备推荐产品/服务，请回复 [NEXT_PHASE:PRODUCT_RECOMMENDATION]

提供清晰、专业的分析，同时避免给出明确的法律建议。`,
        variables: {}
      },
      PRODUCT_RECOMMENDATION: {
        template_content: `你是一个法律咨询助手。你的角色是推荐适当的法律产品和服务。

当前阶段：产品推荐

指令：
1. 基于案例分析，推荐合适的法律服务
2. 解释为什么每个推荐适合他们的情况
3. 提供估计的时间表和考虑因素
4. 如果客户表现出兴趣，准备进行销售转换
5. 如果客户准备继续，请回复 [NEXT_PHASE:SALES_CONVERSION]

在考虑客户需求和预算的同时，提供有用且信息丰富的建议。`,
        variables: {}
      },
      SALES_CONVERSION: {
        template_content: `你是一个法律咨询助手。你的角色是指导客户完成销售转换过程。

当前阶段：销售转换

指令：
1. 解决对推荐服务的任何担忧
2. 提供清晰的参与下一步
3. 解释过程和预期
4. 提供与适当法律专业人士的联系
5. 确保在继续之前回答所有问题

对参与过程提供支持和清晰的说明。`,
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

module.exports = new DeepSeekService();
