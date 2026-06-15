# config/settings.py
"""Application settings and configuration management"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Settings:
    """Application settings loaded from environment variables"""
    
    # ========================================================================
    # LLM Configuration
    # ========================================================================
    
    # OpenAI Configuration
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    openai_max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
    
    # Alternative: Anthropic Claude
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"))
    
    # Which LLM provider to use ('openai' or 'anthropic')
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai"))
    
    # ========================================================================
    # API Configuration
    # ========================================================================
    
    # Financial Data APIs
    alpha_vantage_api_key: str = field(default_factory=lambda: os.getenv("ALPHA_VANTAGE_API_KEY", ""))
    yahoo_finance_enabled: bool = os.getenv("YAHOO_FINANCE_ENABLED", "true").lower() == "true"
    
    # Currency API
    exchangerate_api_key: str = field(default_factory=lambda: os.getenv("EXCHANGERATE_API_KEY", ""))
    
    # Fraud Detection API (optional)
    fraud_detection_api_key: str = field(default_factory=lambda: os.getenv("FRAUD_DETECTION_API_KEY", ""))
    
    # ========================================================================
    # Banking Limits (Default values, can be overridden per user)
    # ========================================================================
    
    # Daily transfer limits
    default_daily_transfer_limit: float = float(os.getenv("DAILY_TRANSFER_LIMIT", "10000.0"))
    default_monthly_transfer_limit: float = float(os.getenv("MONTHLY_TRANSFER_LIMIT", "50000.0"))
    max_single_transfer: float = float(os.getenv("MAX_SINGLE_TRANSFER", "50000.0"))
    
    # Risk thresholds
    risk_high_threshold: int = int(os.getenv("RISK_HIGH_THRESHOLD", "70"))
    risk_medium_threshold: int = int(os.getenv("RISK_MEDIUM_THRESHOLD", "40"))
    
    # Human review required above this amount
    human_review_amount_threshold: float = float(os.getenv("HUMAN_REVIEW_AMOUNT", "10000.0"))
    
    # ========================================================================
    # Retry Configuration
    # ========================================================================
    
    max_retry_attempts: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    retry_backoff_base: float = float(os.getenv("RETRY_BACKOFF_BASE", "1.0"))
    retry_backoff_max: float = float(os.getenv("RETRY_BACKOFF_MAX", "10.0"))
    
    # ========================================================================
    # Database Configuration
    # ========================================================================
    
    # PostgreSQL (optional - for production)
    postgres_host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_database: str = field(default_factory=lambda: os.getenv("POSTGRES_DATABASE", "finance_agent"))
    postgres_user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    postgres_password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))
    
    # Redis (for state persistence)
    redis_host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str = field(default_factory=lambda: os.getenv("REDIS_PASSWORD", ""))
    
    # ========================================================================
    # Application Configuration
    # ========================================================================
    
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    app_debug: bool = os.getenv("APP_DEBUG", "true").lower() == "true"
    app_name: str = "Finance Agentic Chatbot"
    app_version: str = "1.0.0"
    
    # Data directories
    data_dir: str = field(default_factory=lambda: os.getenv("DATA_DIR", "data"))
    logs_dir: str = field(default_factory=lambda: os.getenv("LOGS_DIR", "logs"))
    
    # ========================================================================
    # Security
    # ========================================================================
    
    jwt_secret_key: str = field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "change-me-in-production"))
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Encryption key for sensitive data
    encryption_key: str = field(default_factory=lambda: os.getenv("ENCRYPTION_KEY", ""))
    
    # ========================================================================
    # Feature Flags
    # ========================================================================
    
    enable_fraud_detection: bool = os.getenv("ENABLE_FRAUD_DETECTION", "true").lower() == "true"
    enable_human_review: bool = os.getenv("ENABLE_HUMAN_REVIEW", "true").lower() == "true"
    enable_audit_logging: bool = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
    enable_telemetry: bool = os.getenv("ENABLE_TELEMETRY", "false").lower() == "true"
    
    # ========================================================================
    # Validation Methods
    # ========================================================================
    
    def validate(self) -> bool:
        """Validate required settings"""
        errors = []
        
        # Check LLM configuration
        if self.llm_provider == "openai" and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required when using OpenAI")
        
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required when using Anthropic")
        
        # Check JWT secret in production
        if self.app_env == "production" and self.jwt_secret_key == "change-me-in-production":
            errors.append("JWT_SECRET_KEY must be changed in production")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration dictionary"""
        if self.llm_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model,
                "temperature": self.openai_temperature,
                "max_tokens": self.openai_max_tokens,
            }
        else:
            return {
                "provider": "anthropic",
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model,
                "temperature": self.openai_temperature,
                "max_tokens": self.openai_max_tokens,
            }
    
    def get_limit_for_user(self, user_tier: str = "basic") -> Dict[str, float]:
        """Get limits based on user tier"""
        limits = {
            "basic": {
                "daily_transfer": 5000.0,
                "monthly_transfer": 25000.0,
                "single_transfer": 5000.0,
            },
            "premium": {
                "daily_transfer": 25000.0,
                "monthly_transfer": 100000.0,
                "single_transfer": 25000.0,
            },
            "business": {
                "daily_transfer": 100000.0,
                "monthly_transfer": 500000.0,
                "single_transfer": 100000.0,
            },
            "enterprise": {
                "daily_transfer": 500000.0,
                "monthly_transfer": 2000000.0,
                "single_transfer": 500000.0,
            },
        }
        
        return limits.get(user_tier, limits["basic"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (hides sensitive data)"""
        return {
            "llm_provider": self.llm_provider,
            "openai_model": self.openai_model,
            "app_env": self.app_env,
            "app_debug": self.app_debug,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "daily_transfer_limit": self.default_daily_transfer_limit,
            "monthly_transfer_limit": self.default_monthly_transfer_limit,
            "risk_thresholds": {
                "high": self.risk_high_threshold,
                "medium": self.risk_medium_threshold,
            },
            "features": {
                "fraud_detection": self.enable_fraud_detection,
                "human_review": self.enable_human_review,
                "audit_logging": self.enable_audit_logging,
            },
        }


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings singleton instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.validate()
    return _settings


def reload_settings():
    """Reload settings from environment"""
    global _settings
    _settings = None
    return get_settings()


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("CONFIGURATION SETTINGS TEST")
    print("="*60)
    
    try:
        settings = get_settings()
        
        print("\n✅ Settings loaded successfully!")
        print(f"\n📋 Current Configuration:")
        print(f"   App Name: {settings.app_name}")
        print(f"   Environment: {settings.app_env}")
        print(f"   LLM Provider: {settings.llm_provider}")
        print(f"   Model: {settings.openai_model}")
        print(f"   Daily Transfer Limit: ${settings.default_daily_transfer_limit:,.2f}")
        print(f"   Risk High Threshold: {settings.risk_high_threshold}")
        
        print(f"\n📊 Limits by User Tier:")
        for tier in ["basic", "premium", "business"]:
            limits = settings.get_limit_for_user(tier)
            print(f"   {tier}: ${limits['daily_transfer']:,.0f}/day, ${limits['monthly_transfer']:,.0f}/month")
        
        print(f"\n🔧 Feature Flags:")
        print(f"   Fraud Detection: {settings.enable_fraud_detection}")
        print(f"   Human Review: {settings.enable_human_review}")
        print(f"   Audit Logging: {settings.enable_audit_logging}")
        
    except Exception as e:
        print(f"\n❌ Error loading settings: {e}")