"""
Configuration management for WeChat Automation Service
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Configuration manager for WeChat automation service"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_file = self.base_dir / "config.json"
        self._config = self._load_default_config()
        self._load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'orchestrator': {
                'url': 'ws://localhost:3000',
                'reconnect_attempts': 5,
                'reconnect_delay': 5
            },
            'machine': {
                'id': os.getenv('MACHINE_ID', 'default-machine'),
                'name': os.getenv('MACHINE_NAME', 'WeChat Automation'),
                'capabilities': [
                    'wechat_automation',
                    'desktop_automation',
                    'image_recognition',
                    'text_input',
                    'mouse_control',
                    'keyboard_control'
                ]
            },
            'automation': {
                'screenshot_interval': 1.0,
                'action_delay': 0.5,
                'timeout': 30,
                'max_retries': 3
            },
            'wechat': {
                'exe_path': 'C:\\Program Files\\Tencent\\WeChat\\WeChat.exe',
                'window_title': 'WeChat',
                'auto_start': False
            },
            'logging': {
                'level': 'INFO',
                'file': 'wechat_automation.log',
                'max_size': 10485760,  # 10MB
                'backup_count': 5
            },
            'security': {
                'allow_screenshot': True,
                'allow_file_access': True,
                'restricted_paths': []
            }
        }
    
    def _load_config(self):
        """Load configuration from file and environment"""
        # Load from config file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self._deep_update(self._config, file_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
        
        # Override with environment variables
        env_overrides = {
            'orchestrator.url': os.getenv('ORCHESTRATOR_URL'),
            'machine.id': os.getenv('MACHINE_ID'),
            'machine.name': os.getenv('MACHINE_NAME'),
            'wechat.exe_path': os.getenv('WECHAT_EXE_PATH'),
            'logging.level': os.getenv('LOG_LEVEL')
        }
        
        for key, value in env_overrides.items():
            if value is not None:
                self._set_nested_value(self._config, key, value)
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """Deep update nested dictionary"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """Set nested configuration value using dot notation"""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        current = self._config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        self._set_nested_value(self._config, key, value)
    
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self._config.copy()
    
    def reload(self):
        """Reload configuration from file"""
        self._config = self._load_default_config()
        self._load_config()
