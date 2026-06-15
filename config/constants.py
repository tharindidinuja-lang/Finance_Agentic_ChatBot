# config/constants.py
"""Risk thresholds and limits"""

# Transfer limits
DAILY_TRANSFER_LIMIT = 10000.0  # $10k requires human review
MAX_SINGLE_TRANSFER = 50000.0
FRAUD_AMOUNT_THRESHOLD = 5000.0

# Retry configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = [1, 2, 4]  # Exponential backoff

# Risk scores (0-100)
RISK_THRESHOLD_HIGH = 70
RISK_THRESHOLD_MEDIUM = 40

# Model config
MODEL_NAME = "gpt-4o-mini"
TEMPERATURE = 0.3  # Low temp for deterministic finance tasks