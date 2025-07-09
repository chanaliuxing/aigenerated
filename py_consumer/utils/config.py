"""
Configuration management for Legal Chatbot Python Consumer
"""

import os
from pathlib import Path
from typing import Dict, Any
import json

class Config:
    """Configuration manager for the application"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_file = self.base_dir / "config.json"
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables and config file"""
        # Load from config file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"Error loading config file: {e}")
                self._config = {}
        
        # Override with environment variables
        self._config.update({
            # Database configuration
            'database': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'database': os.getenv('DB_NAME', 'legalbot'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'password'),
                'max_connections': int(os.getenv('DB_MAX_CONNECTIONS', 10))
            },
            
            # Redis configuration
            'redis': {
                'url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
                'enabled': os.getenv('REDIS_ENABLED', 'true').lower() == 'true'
            },
            
            # AI providers
            'ai_providers': {
                'openai': {
                    'api_key': os.getenv('OPENAI_API_KEY', ''),
                    'model': os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
                    'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', 2000)),
                    'temperature': float(os.getenv('OPENAI_TEMPERATURE', 0.7))
                },
                'deepseek': {
                    'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
                    'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
                    'max_tokens': int(os.getenv('DEEPSEEK_MAX_TOKENS', 2000)),
                    'temperature': float(os.getenv('DEEPSEEK_TEMPERATURE', 0.7))
                }
            },
            
            # Application settings
            'app': {
                'name': os.getenv('APP_NAME', 'Legal Chatbot Consumer'),
                'version': os.getenv('APP_VERSION', '1.0.0'),
                'environment': os.getenv('APP_ENV', 'development'),
                'debug': os.getenv('DEBUG', 'false').lower() == 'true',
                'log_level': os.getenv('LOG_LEVEL', 'INFO')
            },
            
            # Processing settings
            'processing': {
                'max_concurrent_requests': int(os.getenv('MAX_CONCURRENT_REQUESTS', 10)),
                'request_timeout': int(os.getenv('REQUEST_TIMEOUT', 30)),
                'retry_attempts': int(os.getenv('RETRY_ATTEMPTS', 3)),
                'retry_delay': int(os.getenv('RETRY_DELAY', 1))
            },
            
            # Workflow settings
            'workflow': {
                'default_phase': os.getenv('DEFAULT_PHASE', 'INFO_COLLECTION'),
                'auto_transition': os.getenv('AUTO_TRANSITION', 'true').lower() == 'true',
                'phase_timeout': int(os.getenv('PHASE_TIMEOUT', 1800))  # 30 minutes
            }
        })
    
    def get(self, key: str, default=None) -> Any:
        """Get configuration value by key"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self._config.get('database', {})
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        return self._config.get('redis', {})
    
    def get_ai_config(self, provider: str) -> Dict[str, Any]:
        """Get AI provider configuration"""
        return self._config.get('ai_providers', {}).get(provider, {})
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration"""
        return self._config.get('app', {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration"""
        return self._config.get('processing', {})
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """Get workflow configuration"""
        return self._config.get('workflow', {})
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get('app.debug', False)
    
    def get_log_level(self) -> str:
        """Get log level"""
        return self.get('app.log_level', 'INFO')
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self._config, updates)
    
    def __getitem__(self, key):
        """Allow dict-like access"""
        return self.get(key)
    
    def __setitem__(self, key, value):
        """Allow dict-like assignment"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
