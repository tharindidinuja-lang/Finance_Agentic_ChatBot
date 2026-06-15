# config/__init__.py
"""Configuration module for Finance Agentic Chatbot"""

from config.settings import Settings, get_settings
from config.constants import *
from config.fraud_rules import FraudRules, FraudRule, get_fraud_rules
from config.logging_config import setup_logging, get_logger

try:
    from config.logging_config import setup_logging, get_logger
except ImportError:
    # Define dummy functions if logging_config doesn't exist
    def setup_logging(*args, **kwargs):
        pass
    def get_logger(name):
        import logging
        return logging.getLogger(name)
    

__all__ = [
    # Settings
    "Settings",
    "get_settings",
    
    # Fraud rules
    "FraudRules",
    "FraudRule",
    "get_fraud_rules",
    
    # Logging
    "setup_logging",
    "get_logger",
]