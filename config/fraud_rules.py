# config/fraud_rules.py
"""Fraud detection rules and suspicious patterns"""

from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class FraudRule:
    """Individual fraud detection rule"""
    name: str
    description: str
    risk_score: int  # 0-100
    weight: float  # Multiplier for this rule
    enabled: bool = True
    
    # Optional custom detection function
    detect_func: Optional[Callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "risk_score": self.risk_score,
            "weight": self.weight,
            "enabled": self.enabled,
        }


class FraudRules:
    """Centralized fraud detection rules configuration"""
    
    def __init__(self):
        self.rules: List[FraudRule] = []
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialize all fraud detection rules"""
        
        # ====================================================================
        # Amount-based rules
        # ====================================================================
        
        self.rules.append(FraudRule(
            name="large_transaction",
            description="Transaction amount exceeds $10,000",
            risk_score=40,
            weight=1.0,
        ))
        
        self.rules.append(FraudRule(
            name="very_large_transaction",
            description="Transaction amount exceeds $25,000",
            risk_score=60,
            weight=1.2,
        ))
        
        self.rules.append(FraudRule(
            name="extremely_large_transaction",
            description="Transaction amount exceeds $50,000",
            risk_score=80,
            weight=1.5,
        ))
        
        self.rules.append(FraudRule(
            name="round_number_transaction",
            description="Transaction amount is a round number (possible structuring)",
            risk_score=10,
            weight=0.5,
        ))
        
        # ====================================================================
        # Velocity-based rules (too many transactions)
        # ====================================================================
        
        self.rules.append(FraudRule(
            name="high_velocity_daily",
            description="More than 10 transactions in 24 hours",
            risk_score=30,
            weight=1.0,
        ))
        
        self.rules.append(FraudRule(
            name="high_velocity_hourly",
            description="More than 5 transactions in 1 hour",
            risk_score=40,
            weight=1.2,
        ))
        
        self.rules.append(FraudRule(
            name="rapid_successive_transfers",
            description="Multiple transfers within minutes",
            risk_score=50,
            weight=1.3,
        ))
        
        # ====================================================================
        # Recipient-based rules
        # ====================================================================
        
        self.rules.append(FraudRule(
            name="new_recipient",
            description="Transaction to a new recipient",
            risk_score=25,
            weight=1.0,
        ))
        
        self.rules.append(FraudRule(
            name="international_recipient",
            description="Transaction to international account",
            risk_score=35,
            weight=1.1,
        ))
        
        self.rules.append(FraudRule(
            name="high_risk_recipient",
            description="Recipient is on high-risk list",
            risk_score=70,
            weight=1.5,
        ))
        
        self.rules.append(FraudRule(
            name="crypto_recipient",
            description="Transaction to cryptocurrency exchange",
            risk_score=65,
            weight=1.4,
        ))
        
        # ====================================================================
        # Time-based rules
        # ====================================================================
        
        self.rules.append(FraudRule(
            name="off_hours_transaction",
            description="Transaction outside business hours (9pm-6am)",
            risk_score=20,
            weight=0.8,
        ))
        
        self.rules.append(FraudRule(
            name="weekend_transaction",
            description="Transaction on weekend",
            risk_score=10,
            weight=0.6,
        ))
        
        self.rules.append(FraudRule(
            name="holiday_transaction",
            description="Transaction on bank holiday",
            risk_score=15,
            weight=0.7,
        ))
        
        # ====================================================================
        # Pattern-based rules
        # ====================================================================
        
        self.rules.append(FraudRule(
            name="structuring_pattern",
            description="Multiple transactions just below reporting threshold",
            risk_score=60,
            weight=1.3,
        ))
        
        self.rules.append(FraudRule(
            name="balance_chasing",
            description="Transactions that bring balance close to zero",
            risk_score=45,
            weight=1.1,
        ))
        
        self.rules.append(FraudRule(
            name="unusual_location",
            description="Transaction from unusual geographic location",
            risk_score=30,
            weight=1.0,
        ))
        
        self.rules.append(FraudRule(
            name="unusual_device",
            description="Transaction from unrecognized device",
            risk_score=25,
            weight=0.9,
        ))
        
        # ====================================================================
        # History-based rules
        # ====================================================================
        
        self.rules.append(FraudRule(
            name="first_time_large_transfer",
            description="First large transfer from this account",
            risk_score=35,
            weight=1.1,
        ))
        
        self.rules.append(FraudRule(
            name="amount_anomaly",
            description="Amount significantly higher than average",
            risk_score=40,
            weight=1.2,
        ))
        
        self.rules.append(FraudRule(
            name="failed_login_before_transfer",
            description="Failed login attempts before transaction",
            risk_score=50,
            weight=1.3,
        ))
        
        self.rules.append(FraudRule(
            name="recent_password_change",
            description="Recent password change before transaction",
            risk_score=30,
            weight=1.0,
        ))
    
    def get_enabled_rules(self) -> List[FraudRule]:
        """Get all enabled rules"""
        return [rule for rule in self.rules if rule.enabled]
    
    def get_rule_by_name(self, name: str) -> Optional[FraudRule]:
        """Get a specific rule by name"""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None
    
    def enable_rule(self, name: str):
        """Enable a specific rule"""
        rule = self.get_rule_by_name(name)
        if rule:
            rule.enabled = True
    
    def disable_rule(self, name: str):
        """Disable a specific rule"""
        rule = self.get_rule_by_name(name)
        if rule:
            rule.enabled = False
    
    def calculate_max_risk_score(self) -> int:
        """Calculate maximum possible risk score from all enabled rules"""
        total = 0
        for rule in self.get_enabled_rules():
            total += rule.risk_score
        return min(total, 100)  # Cap at 100
    
    def get_risk_for_amount(self, amount: float) -> tuple:
        """Get risk score and rule name for a given amount"""
        if amount >= 50000:
            return 80, "extremely_large_transaction"
        elif amount >= 25000:
            return 60, "very_large_transaction"
        elif amount >= 10000:
            return 40, "large_transaction"
        elif amount % 1000 == 0 and amount > 0:
            return 10, "round_number_transaction"
        return 0, None
    
    def get_risk_for_recipient(self, recipient: str) -> tuple:
        """Get risk score for a recipient based on keywords"""
        recipient_lower = recipient.lower()
        
        # High risk recipients
        high_risk_keywords = [
            "crypto", "bitcoin", "ethereum", "binance", "coinbase",
            "offshore", "cayman", "panama", "tax haven"
        ]
        
        for keyword in high_risk_keywords:
            if keyword in recipient_lower:
                return 70, "high_risk_recipient"
        
        # Crypto exchanges
        crypto_keywords = ["crypto", "coin", "exchange", "wallet"]
        for keyword in crypto_keywords:
            if keyword in recipient_lower:
                return 65, "crypto_recipient"
        
        # International check (simple heuristic)
        if any(c.isalpha() and ord(c) > 127 for c in recipient):
            return 35, "international_recipient"
        
        return 0, None
    
    def get_risk_for_time(self) -> tuple:
        """Get risk score based on current time"""
        now = datetime.now()
        
        # Check for off-hours (9 PM to 6 AM)
        if now.hour >= 21 or now.hour <= 6:
            return 20, "off_hours_transaction"
        
        # Check weekend
        if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return 10, "weekend_transaction"
        
        return 0, None
    
    def get_velocity_risk(self, daily_count: int, hourly_count: int) -> List[tuple]:
        """Get risk scores based on transaction velocity"""
        risks = []
        
        if daily_count > 10:
            risks.append((30, "high_velocity_daily"))
        elif daily_count > 5:
            risks.append((15, "moderate_velocity_daily"))
        
        if hourly_count > 5:
            risks.append((40, "high_velocity_hourly"))
        elif hourly_count > 3:
            risks.append((20, "moderate_velocity_hourly"))
        
        return risks
    
    def calculate_total_risk(self, rule_contributions: List[tuple]) -> int:
        """
        Calculate total risk score from multiple rule contributions.
        
        Args:
            rule_contributions: List of (risk_score, rule_name) tuples
            
        Returns:
            Total risk score (0-100)
        """
        total = 0
        applied_weights = {}
        
        for risk_score, rule_name in rule_contributions:
            rule = self.get_rule_by_name(rule_name)
            if rule and rule.enabled:
                weight = rule.weight
                contribution = int(risk_score * weight)
                total += contribution
                applied_weights[rule_name] = weight
        
        # Cap at 100
        return min(total, 100)
    
    def get_all_rules_summary(self) -> Dict[str, Any]:
        """Get summary of all fraud rules"""
        enabled_count = len(self.get_enabled_rules())
        
        return {
            "total_rules": len(self.rules),
            "enabled_rules": enabled_count,
            "disabled_rules": len(self.rules) - enabled_count,
            "max_possible_risk": self.calculate_max_risk_score(),
            "rules_by_category": self._group_rules_by_category(),
        }
    
    def _group_rules_by_category(self) -> Dict[str, List[str]]:
        """Group rules by their category"""
        categories = {
            "amount": ["large_transaction", "very_large_transaction", "extremely_large_transaction", 
                      "round_number_transaction"],
            "velocity": ["high_velocity_daily", "high_velocity_hourly", "rapid_successive_transfers"],
            "recipient": ["new_recipient", "international_recipient", "high_risk_recipient", "crypto_recipient"],
            "time": ["off_hours_transaction", "weekend_transaction", "holiday_transaction"],
            "pattern": ["structuring_pattern", "balance_chasing", "unusual_location", "unusual_device"],
            "history": ["first_time_large_transfer", "amount_anomaly", "failed_login_before_transfer", 
                       "recent_password_change"],
        }
        
        return categories


# Singleton instance
_fraud_rules: Optional[FraudRules] = None


def get_fraud_rules() -> FraudRules:
    """Get fraud rules singleton instance"""
    global _fraud_rules
    if _fraud_rules is None:
        _fraud_rules = FraudRules()
    return _fraud_rules


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("FRAUD RULES TEST")
    print("="*60)
    
    rules = get_fraud_rules()
    
    print(f"\n Fraud Rules Summary:")
    summary = rules.get_all_rules_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    print(f"\n Testing Rule Detection:")
    
    # Test amount-based
    for amount in [500, 8000, 15000, 30000, 60000]:
        risk, rule = rules.get_risk_for_amount(amount)
        if rule:
            print(f"   Amount ${amount:,.0f}: {rule} (+{risk} points)")
    
    # Test recipient-based
    for recipient in ["John Smith", "Binance Exchange", "Offshore Bank Ltd"]:
        risk, rule = rules.get_risk_for_recipient(recipient)
        if rule:
            print(f"   Recipient '{recipient}': {rule} (+{risk} points)")
    
    # Test time-based
    risk, rule = rules.get_risk_for_time()
    if rule:
        print(f"   Current time: {rule} (+{risk} points)")
    
    # Test velocity
    print(f"\n Velocity Risk Examples:")
    for daily, hourly in [(3, 1), (8, 4), (15, 8)]:
        risks = rules.get_velocity_risk(daily, hourly)
        if risks:
            print(f"   Daily:{daily}, Hourly:{hourly} → {risks}")
    
    # Test total risk calculation
    print(f"\n Total Risk Calculation Example:")
    contributions = [
        (40, "large_transaction"),
        (25, "new_recipient"),
        (20, "off_hours_transaction"),
        (30, "high_velocity_daily"),
    ]
    total = rules.calculate_total_risk(contributions)
    print(f"   Contributions: {contributions}")
    print(f"   Total Risk Score: {total}/100")
    
    print("\n Fraud rules test complete!")