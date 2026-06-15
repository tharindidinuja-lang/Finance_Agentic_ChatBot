# config/logging_config.py
"""Logging configuration for the Finance Agentic Chatbot"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_dir: str = "logs", 
                  enable_console: bool = True, enable_file: bool = False,
                  enable_json: bool = False):
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        enable_console: Enable console logging
        enable_file: Enable file logging
        enable_json: Enable JSON format for file logs
    """
    
    # Convert string log level to int
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplication
    root_logger.handlers.clear()
    
    # Create formatter
    console_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    console_formatter = logging.Formatter(console_format)
    
    # Console Handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File Handler (optional)
    if enable_file:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        log_file = Path(log_dir) / f"finance_agent_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s'
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, Console: {enable_console}, File: {enable_file}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Simple test
if __name__ == "__main__":
    setup_logging(log_level="DEBUG")
    logger = get_logger("test")
    logger.debug("Debug message test")
    logger.info("Info message test")
    logger.warning("Warning message test")
    print("Logging test complete!")