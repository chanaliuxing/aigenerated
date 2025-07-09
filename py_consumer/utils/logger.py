"""
Logging configuration for Legal Chatbot Python Consumer
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(level=logging.INFO, log_file=None):
    """
    Setup logging configuration
    
    Args:
        level: Logging level
        log_file: Optional log file path
    
    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create logger
    logger = logging.getLogger('legal_chatbot_consumer')
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_file = logs_dir / f"py_consumer_{datetime.now().strftime('%Y%m%d')}.log"
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_file = logs_dir / f"py_consumer_error_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger

def get_logger(name=None):
    """Get logger instance"""
    if name is None:
        name = 'legal_chatbot_consumer'
    return logging.getLogger(name)

# Module-level logger
logger = get_logger()
