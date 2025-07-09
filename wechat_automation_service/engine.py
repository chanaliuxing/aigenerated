#!/usr/bin/env python3
"""
Workflow Engine for WeChat Automation
Handles workflow execution and management
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from basic_actions import BasicActions

logger = logging.getLogger(__name__)

@dataclass
class WorkflowStep:
    """Represents a single workflow step"""
    id: str
    action: str
    parameters: Dict[str, Any]
    timeout: int = 30
    retry_count: int = 3
    condition: Optional[str] = None

@dataclass
class WorkflowContext:
    """Workflow execution context"""
    workflow_id: str
    session_id: str
    user_id: str
    variables: Dict[str, Any]
    step_results: Dict[str, Any]
    current_step: int = 0
    status: str = "pending"
    created_at: datetime = None
    updated_at: datetime = None

class WorkflowEngine:
    """Main workflow execution engine"""
    
    def __init__(self):
        self.active_workflows: Dict[str, WorkflowContext] = {}
        self.workflow_templates: Dict[str, Dict] = {}
        self.basic_actions = BasicActions()
        self.last_activity = datetime.now()
        
    async def initialize(self):
        """Initialize the workflow engine"""
        try:
            # Initialize basic actions
            await self.basic_actions.initialize()
            
            # Load workflow templates
            await self.load_workflow_templates()
            
            logger.info("Workflow engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize workflow engine: {e}")
            raise
    
    async def load_workflow_templates(self):
        """Load workflow templates from configuration"""
        # Default workflow templates
        self.workflow_templates = {
            "send_message": {
                "name": "Send WeChat Message",
                "description": "Send a message to a WeChat contact",
                "steps": [
                    {
                        "id": "open_wechat",
                        "action": "open_application",
                        "parameters": {"app_name": "WeChat"}
                    },
                    {
                        "id": "search_contact",
                        "action": "search_contact",
                        "parameters": {"contact_name": "{{contact_name}}"}
                    },
                    {
                        "id": "send_message",
                        "action": "send_message",
                        "parameters": {"message": "{{message}}"}
                    }
                ]
            },
            "receive_message": {
                "name": "Monitor WeChat Messages",
                "description": "Monitor incoming WeChat messages",
                "steps": [
                    {
                        "id": "monitor_messages",
                        "action": "monitor_messages",
                        "parameters": {"timeout": 60}
                    }
                ]
            },
            "auto_reply": {
                "name": "Auto Reply Messages",
                "description": "Automatically reply to incoming messages",
                "steps": [
                    {
                        "id": "monitor_messages",
                        "action": "monitor_messages",
                        "parameters": {"timeout": 60}
                    },
                    {
                        "id": "generate_reply",
                        "action": "generate_reply",
                        "parameters": {"message": "{{incoming_message}}"}
                    },
                    {
                        "id": "send_reply",
                        "action": "send_message",
                        "parameters": {"message": "{{reply_message}}"}
                    }
                ]
            }
        }
        
        logger.info(f"Loaded {len(self.workflow_templates)} workflow templates")
    
    async def execute_workflow(self, workflow_data: Dict, context: Dict) -> Dict:
        """Execute a workflow"""
        try:
            workflow_id = str(uuid.uuid4())
            
            # Create workflow context
            workflow_context = WorkflowContext(
                workflow_id=workflow_id,
                session_id=context.get('session_id', ''),
                user_id=context.get('user_id', ''),
                variables=context.get('variables', {}),
                step_results={},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Store active workflow
            self.active_workflows[workflow_id] = workflow_context
            
            # Parse workflow steps
            steps = self._parse_workflow_steps(workflow_data)
            
            # Execute workflow steps
            result = await self._execute_workflow_steps(workflow_context, steps)
            
            # Update status
            workflow_context.status = "completed" if result['success'] else "failed"
            workflow_context.updated_at = datetime.now()
            
            # Clean up
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            self.last_activity = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return {
                'success': False,
                'error': str(e),
                'workflow_id': workflow_id
            }
    
    def _parse_workflow_steps(self, workflow_data: Dict) -> List[WorkflowStep]:
        """Parse workflow data into steps"""
        steps = []
        
        if 'template' in workflow_data:
            # Use template
            template_name = workflow_data['template']
            if template_name in self.workflow_templates:
                template = self.workflow_templates[template_name]
                step_data = template.get('steps', [])
            else:
                raise ValueError(f"Unknown workflow template: {template_name}")
        else:
            # Use custom steps
            step_data = workflow_data.get('steps', [])
        
        for step in step_data:
            workflow_step = WorkflowStep(
                id=step.get('id', str(uuid.uuid4())),
                action=step.get('action'),
                parameters=step.get('parameters', {}),
                timeout=step.get('timeout', 30),
                retry_count=step.get('retry_count', 3),
                condition=step.get('condition')
            )
            steps.append(workflow_step)
        
        return steps
    
    async def _execute_workflow_steps(self, context: WorkflowContext, steps: List[WorkflowStep]) -> Dict:
        """Execute workflow steps"""
        results = []
        
        for i, step in enumerate(steps):
            context.current_step = i
            context.updated_at = datetime.now()
            
            # Check condition if specified
            if step.condition and not self._evaluate_condition(step.condition, context):
                logger.info(f"Skipping step {step.id} due to condition: {step.condition}")
                continue
            
            # Execute step with retries
            step_result = await self._execute_step_with_retries(step, context)
            
            # Store step result
            context.step_results[step.id] = step_result
            results.append(step_result)
            
            # Check if step failed and should stop workflow
            if not step_result.get('success', False):
                return {
                    'success': False,
                    'error': f"Step {step.id} failed: {step_result.get('error', 'Unknown error')}",
                    'results': results,
                    'workflow_id': context.workflow_id
                }
        
        return {
            'success': True,
            'results': results,
            'workflow_id': context.workflow_id
        }
    
    async def _execute_step_with_retries(self, step: WorkflowStep, context: WorkflowContext) -> Dict:
        """Execute a single step with retries"""
        for attempt in range(step.retry_count):
            try:
                logger.info(f"Executing step {step.id} (attempt {attempt + 1}/{step.retry_count})")
                
                # Substitute variables in parameters
                parameters = self._substitute_variables(step.parameters, context)
                
                # Execute the action
                result = await self._execute_action(step.action, parameters, step.timeout)
                
                if result.get('success', False):
                    logger.info(f"Step {step.id} completed successfully")
                    return result
                else:
                    logger.warning(f"Step {step.id} failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error executing step {step.id}: {e}")
                result = {'success': False, 'error': str(e)}
            
            if attempt < step.retry_count - 1:
                await asyncio.sleep(1)  # Wait before retry
        
        return result
    
    async def _execute_action(self, action: str, parameters: Dict, timeout: int) -> Dict:
        """Execute a specific action"""
        try:
            # Get action method
            action_method = getattr(self.basic_actions, action, None)
            if not action_method:
                return {'success': False, 'error': f"Unknown action: {action}"}
            
            # Execute action with timeout
            result = await asyncio.wait_for(
                action_method(**parameters), 
                timeout=timeout
            )
            
            return result
            
        except asyncio.TimeoutError:
            return {'success': False, 'error': f"Action {action} timed out after {timeout} seconds"}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _substitute_variables(self, parameters: Dict, context: WorkflowContext) -> Dict:
        """Substitute variables in parameters"""
        def substitute_value(value):
            if isinstance(value, str):
                # Simple variable substitution
                for var_name, var_value in context.variables.items():
                    value = value.replace(f"{{{{{var_name}}}}}", str(var_value))
                
                # Step result substitution
                for step_id, step_result in context.step_results.items():
                    if isinstance(step_result, dict) and 'data' in step_result:
                        value = value.replace(f"{{{{{step_id}}}}}", str(step_result['data']))
                
                return value
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            else:
                return value
        
        return {k: substitute_value(v) for k, v in parameters.items()}
    
    def _evaluate_condition(self, condition: str, context: WorkflowContext) -> bool:
        """Evaluate a condition"""
        # Simple condition evaluation (can be extended)
        try:
            # Replace variables in condition
            condition = self._substitute_variables({'condition': condition}, context)['condition']
            
            # Basic condition evaluation
            if condition.lower() in ['true', '1', 'yes']:
                return True
            elif condition.lower() in ['false', '0', 'no']:
                return False
            else:
                # Try to evaluate as Python expression (be careful with security)
                return bool(eval(condition))
                
        except Exception as e:
            logger.warning(f"Error evaluating condition '{condition}': {e}")
            return False
    
    async def stop_workflow(self, workflow_id: str):
        """Stop a running workflow"""
        if workflow_id in self.active_workflows:
            context = self.active_workflows[workflow_id]
            context.status = "stopped"
            context.updated_at = datetime.now()
            
            # Clean up
            del self.active_workflows[workflow_id]
            
            logger.info(f"Workflow {workflow_id} stopped")
    
    async def stop_all_workflows(self):
        """Stop all running workflows"""
        workflow_ids = list(self.active_workflows.keys())
        for workflow_id in workflow_ids:
            await self.stop_workflow(workflow_id)
        
        logger.info("All workflows stopped")
    
    async def get_active_workflows(self) -> List[Dict]:
        """Get list of active workflows"""
        return [
            {
                'workflow_id': context.workflow_id,
                'session_id': context.session_id,
                'user_id': context.user_id,
                'status': context.status,
                'current_step': context.current_step,
                'created_at': context.created_at.isoformat() if context.created_at else None,
                'updated_at': context.updated_at.isoformat() if context.updated_at else None
            }
            for context in self.active_workflows.values()
        ]
    
    def get_capabilities(self) -> List[str]:
        """Get list of supported capabilities"""
        return [
            'send_message',
            'receive_message',
            'auto_reply',
            'search_contact',
            'monitor_messages',
            'open_application',
            'take_screenshot',
            'click_element',
            'type_text'
        ]
    
    def get_last_activity(self) -> str:
        """Get last activity timestamp"""
        return self.last_activity.isoformat()
