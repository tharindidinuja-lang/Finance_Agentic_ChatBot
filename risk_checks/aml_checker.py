# risk_checks/aml_checker.py
"""Anti-Money Laundering (AML) compliance checker"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
from enum import Enum


class AMLRiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AMLAlert:
    """AML alert structure"""
    alert_id: str
    rule_name: str
    risk_level: AMLRiskLevel
    description: str
    triggered_at: datetime
    transaction_details: Dict[str, Any]
    recommended_action: str


class AMLChecker:
    """
    Anti-Money Laundering compliance checker.
    Implements rules for detecting suspicious financial activities.
    """
    
    def __init__(self):
        self.alerts: List[AMLAlert] = []
        self.sanctions_list = self._load_sanctions_list()
        self.high_risk_countries = self._load_high_risk_countries()
    
    def _load_sanctions_list(self) -> set:
        """Load sanctioned entities list"""
        # In production, this would load from OFAC or similar database
        return {
            "NORTH_KOREA_NATIONAL_BANK",
            "IRAN_OIL_COMPANY",
            "SYRIAN_GOVERNMENT_ENTITY",
            # Add more sanctioned entities
        }
    
    def _load_high_risk_countries(self) -> set:
        """Load high-risk jurisdictions (FATF list)"""
        return {
            "IRAN", "NORTH_KOREA", "SYRIA", "MYANMAR", 
            "YEMEN", "VENEZUELA", "RUSSIA", "BELARUS"
        }
    
    def check_transaction(self, transaction: Dict[str, Any], user_history: List[Dict] = None) -> Tuple[float, List[AMLAlert]]:
        """
        Perform AML checks on a transaction.
        
        Args:
            transaction: Transaction details
            user_history: User's transaction history
            
        Returns:
            Tuple of (risk_score, list_of_alerts)
        """
        risk_score = 0
        alerts = []
        
        # Check 1: Transaction amount structuring
        struct_risk, struct_alerts = self._check_structuring(transaction, user_history)
        risk_score += struct_risk
        alerts.extend(struct_alerts)
        
        # Check 2: Suspicious recipients
        recipient_risk, recipient_alerts = self._check_recipient(transaction)
        risk_score += recipient_risk
        alerts.extend(recipient_alerts)
        
        # Check 3: Geographic risk
        geo_risk, geo_alerts = self._check_geographic(transaction)
        risk_score += geo_risk
        alerts.extend(geo_alerts)
        
        # Check 4: Rapid movement of funds
        velocity_risk, velocity_alerts = self._check_fund_velocity(transaction, user_history)
        risk_score += velocity_risk
        alerts.extend(velocity_alerts)
        
        # Check 5: Round number pattern
        round_risk, round_alerts = self._check_round_numbers(transaction)
        risk_score += round_risk
        alerts.extend(round_alerts)
        
        # Check 6: Unusual pattern for user
        pattern_risk, pattern_alerts = self._check_unusual_pattern(transaction, user_history)
        risk_score += pattern_risk
        alerts.extend(pattern_alerts)
        
        # Cap risk score at 100
        risk_score = min(risk_score, 100)
        
        return risk_score, alerts
    
    def _check_structuring(self, transaction: Dict, history: List[Dict]) -> Tuple[int, List[AMLAlert]]:
        """
        Check for transaction structuring (smurfing).
        Multiple transactions just below reporting threshold.
        """
        alerts = []
        risk_score = 0
        amount = transaction.get("amount", 0)
        reporting_threshold = 10000  # $10,000 CTR threshold
        
        # Check if this transaction is just under threshold
        if reporting_threshold - amount < 1000 and amount < reporting_threshold:
            risk_score += 15
            alerts.append(AMLAlert(
                alert_id=self._generate_alert_id(),
                rule_name="structuring_near_threshold",
                risk_level=AMLRiskLevel.MEDIUM,
                description=f"Transaction amount ${amount:,.2f} is just under ${reporting_threshold:,.2f} reporting threshold",
                triggered_at=datetime.now(),
                transaction_details=transaction,
                recommended_action="Review for potential structuring"
            ))
        
        # Check for multiple transactions near threshold
        if history:
            recent_threshold_txs = [
                tx for tx in history[-5:] 
                if reporting_threshold - tx.get("amount", 0) < 1000
            ]
            
            if len(recent_threshold_txs) >= 3:
                risk_score += 30
                alerts.append(AMLAlert(
                    alert_id=self._generate_alert_id(),
                    rule_name="multiple_threshold_transactions",
                    risk_level=AMLRiskLevel.HIGH,
                    description=f"Multiple transactions ({len(recent_threshold_txs)}) near ${reporting_threshold:,.2f} threshold",
                    triggered_at=datetime.now(),
                    transaction_details=transaction,
                    recommended_action="File SAR (Suspicious Activity Report)"
                ))
        
        return risk_score, alerts
    
    def _check_recipient(self, transaction: Dict) -> Tuple[int, List[AMLAlert]]:
        """Check if recipient is on sanctions list or high-risk"""
        alerts = []
        risk_score = 0
        
        recipient = transaction.get("recipient", "")
        recipient_upper = recipient.upper()
        
        # Check sanctions list
        for sanctioned in self.sanctions_list:
            if sanctioned in recipient_upper:
                risk_score = 100  # Maximum risk
                alerts.append(AMLAlert(
                    alert_id=self._generate_alert_id(),
                    rule_name="sanctions_violation",
                    risk_level=AMLRiskLevel.CRITICAL,
                    description=f"Transaction to sanctioned entity: {sanctioned}",
                    triggered_at=datetime.now(),
                    transaction_details=transaction,
                    recommended_action="BLOCK IMMEDIATELY, file report"
                ))
                return risk_score, alerts
        
        # Check for shell company indicators
        shell_indicators = ["SHELL", "OFFSHORE", "HOLDING", "INVESTMENT LTD", "TRUST"]
        for indicator in shell_indicators:
            if indicator in recipient_upper:
                risk_score += 20
                alerts.append(AMLAlert(
                    alert_id=self._generate_alert_id(),
                    rule_name="shell_company_risk",
                    risk_level=AMLRiskLevel.MEDIUM,
                    description=f"Recipient appears to be shell company: {recipient}",
                    triggered_at=datetime.now(),
                    transaction_details=transaction,
                    recommended_action="Request beneficial ownership information"
                ))
                break
        
        # Check for PEP indicators (Politically Exposed Persons)
        pep_indicators = ["PRESIDENT", "MINISTER", "AMBASSADOR", "GOVERNOR", "SENATOR"]
        for indicator in pep_indicators:
            if indicator in recipient_upper:
                risk_score += 35
                alerts.append(AMLAlert(
                    alert_id=self._generate_alert_id(),
                    rule_name="pep_related",
                    risk_level=AMLRiskLevel.HIGH,
                    description=f"Recipient may be Politically Exposed Person (PEP)",
                    triggered_at=datetime.now(),
                    transaction_details=transaction,
                    recommended_action="Enhanced due diligence required"
                ))
                break
        
        return min(risk_score, 100), alerts
    
    def _check_geographic(self, transaction: Dict) -> Tuple[int, List[AMLAlert]]:
        """Check geographic risk factors"""
        alerts = []
        risk_score = 0
        
        recipient_location = transaction.get("recipient_location", "")
        sender_location = transaction.get("sender_location", "")
        
        # Check high-risk countries
        for country in self.high_risk_countries:
            if country in recipient_location.upper():
                risk_score += 40
                alerts.append(AMLAlert(
                    alert_id=self._generate_alert_id(),
                    rule_name="high_risk_jurisdiction",
                    risk_level=AMLRiskLevel.HIGH,
                    description=f"Transaction to high-risk jurisdiction: {country}",
                    triggered_at=datetime.now(),
                    transaction_details=transaction,
                    recommended_action="Enhanced due diligence"
                ))
                break
        
        # Check for unusual routing (through multiple countries)
        routing_countries = transaction.get("routing_countries", [])
        if len(routing_countries) > 2:
            risk_score += 25
            alerts.append(AMLAlert(
                alert_id=self._generate_alert_id(),
                rule_name="complex_routing",
                risk_level=AMLRiskLevel.MEDIUM,
                description=f"Transaction routed through {len(routing_countries)} countries",
                triggered_at=datetime.now(),
                transaction_details=transaction,
                recommended_action="Review routing justification"
            ))
        
        return risk_score, alerts
    
    def _check_fund_velocity(self, transaction: Dict, history: List[Dict]) -> Tuple[int, List[AMLAlert]]:
        """Check rapid movement of funds"""
        alerts = []
        risk_score = 0
        
        if not history:
            return risk_score, alerts
        
        # Calculate total outflow in last 24 hours
        last_24h = datetime.now() - timedelta(hours=24)
        recent_outflows = sum(
            tx.get("amount", 0) 
            for tx in history[-10:] 
            if tx.get("type") == "debit" or tx.get("type") == "transfer"
        )
        
        current_amount = transaction.get("amount", 0)
        total_recent = recent_outflows + current_amount
        
        # Check if total recent outflow exceeds threshold
        if total_recent > 50000:
            risk_score += 30
            alerts.append(AMLAlert(
                alert_id=self._generate_alert_id(),
                rule_name="rapid_fund_movement",
                risk_level=AMLRiskLevel.HIGH,
                description=f"Total outflow of ${total_recent:,.2f} in last 24 hours",
                triggered_at=datetime.now(),
                transaction_details=transaction,
                recommended_action="Verify source of funds"
            ))
        
        return risk_score, alerts
    
    def _check_round_numbers(self, transaction: Dict) -> Tuple[int, List[AMLAlert]]:
        """Check for round number patterns (potential structuring)"""
        alerts = []
        risk_score = 0
        
        amount = transaction.get("amount", 0)
        
        # Check if amount is a round number
        if amount % 1000 == 0 and amount > 0:
            risk_score += 5
            alerts.append(AMLAlert(
                alert_id=self._generate_alert_id(),
                rule_name="round_number_transaction",
                risk_level=AMLRiskLevel.LOW,
                description=f"Transaction amount ${amount:,.2f} is a round number",
                triggered_at=datetime.now(),
                transaction_details=transaction,
                recommended_action="Monitor for pattern"
            ))
        
        # Check for numbers just below thresholds
        thresholds = [3000, 5000, 10000, 15000, 20000, 25000, 30000]
        for threshold in thresholds:
            if threshold - amount < 100 and amount < threshold and amount > 0:
                risk_score += 10
                alerts.append(AMLAlert(
                    alert_id=self._generate_alert_id(),
                    rule_name="structuring_suspicion",
                    risk_level=AMLRiskLevel.MEDIUM,
                    description=f"Amount ${amount:,.2f} is just below ${threshold:,.2f} threshold",
                    triggered_at=datetime.now(),
                    transaction_details=transaction,
                    recommended_action="Review for potential structuring"
                ))
                break
        
        return risk_score, alerts
    
    def _check_unusual_pattern(self, transaction: Dict, history: List[Dict]) -> Tuple[int, List[AMLAlert]]:
        """Check for unusual patterns compared to user history"""
        alerts = []
        risk_score = 0
        
        if not history or len(history) < 5:
            return risk_score, alerts
        
        # Calculate user's average transaction amount
        avg_amount = sum(tx.get("amount", 0) for tx in history[-20:]) / len(history[-20:])
        current_amount = transaction.get("amount", 0)
        
        # Check for sudden increase
        if current_amount > avg_amount * 3:
            risk_score += 25
            alerts.append(AMLAlert(
                alert_id=self._generate_alert_id(),
                rule_name="sudden_amount_increase",
                risk_level=AMLRiskLevel.MEDIUM,
                description=f"Transaction amount ${current_amount:,.2f} is 3x higher than average (${avg_amount:,.2f})",
                triggered_at=datetime.now(),
                transaction_details=transaction,
                recommended_action="Request explanation for increase"
            ))
        
        return risk_score, alerts
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        return f"AML_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.alerts)}"


# Test
if __name__ == "__main__":
    print("="*60)
    print("AML CHECKER TEST")
    print("="*60)
    
    aml = AMLChecker()
    
    # Test transaction
    test_transaction = {
        "amount": 9500.00,
        "recipient": "Offshore Investments Ltd",
        "recipient_location": "Cayman Islands",
        "type": "wire_transfer"
    }
    
    risk_score, alerts = aml.check_transaction(test_transaction)
    
    print(f"\nRisk Score: {risk_score}/100")
    print(f"Alerts Triggered: {len(alerts)}")
    
    for alert in alerts:
        print(f"\n  Alert: {alert.rule_name}")
        print(f"    Risk Level: {alert.risk_level.value}")
        print(f"    Description: {alert.description}")
        print(f"    Action: {alert.recommended_action}")