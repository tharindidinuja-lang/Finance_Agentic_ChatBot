# tools/fraud_detection.py
"""ML-based fraud detection for transactions"""

from tools.base_tool import BaseTool
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random


class FraudDetectionTool(BaseTool):
    """Detect fraudulent transactions using rule-based and ML models"""
    
    @property
    def name(self) -> str:
        return "detect_fraud"
    
    @property
    def description(self) -> str:
        return "Analyze transaction for potential fraud using multiple detection methods"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier"
                },
                "amount": {
                    "type": "number",
                    "description": "Transaction amount"
                },
                "recipient": {
                    "type": "string",
                    "description": "Recipient account"
                },
                "transaction_type": {
                    "type": "string",
                    "description": "Type of transaction",
                    "enum": ["transfer", "withdrawal", "payment"]
                },
                "user_history": {
                    "type": "object",
                    "description": "User's transaction history for pattern analysis",
                    "default": {}
                }
            },
            "required": ["user_id", "amount", "recipient"]
        }
    
    def execute(self, user_id: str, amount: float, recipient: str, 
                transaction_type: str = "transfer", user_history: Dict = None, **kwargs) -> Dict[str, Any]:
        """Run fraud detection algorithms"""
        
        risk_score = 0
        risk_factors = []
        
        # Factor 1: Amount anomaly
        amount_risk = self._check_amount_anomaly(user_id, amount, user_history)
        risk_score += amount_risk["score"]
        if amount_risk["score"] > 0:
            risk_factors.append(amount_risk["reason"])
        
        # Factor 2: Time anomaly (e.g., 3 AM transaction)
        time_risk = self._check_time_anomaly()
        risk_score += time_risk["score"]
        if time_risk["score"] > 0:
            risk_factors.append(time_risk["reason"])
        
        # Factor 3: Location anomaly (simulated)
        location_risk = self._check_location_anomaly()
        risk_score += location_risk["score"]
        if location_risk["score"] > 0:
            risk_factors.append(location_risk["reason"])
        
        # Factor 4: Recipient risk
        recipient_risk = self._check_recipient_risk(recipient)
        risk_score += recipient_risk["score"]
        if recipient_risk["score"] > 0:
            risk_factors.append(recipient_risk["reason"])
        
        # Factor 5: Velocity (too many transactions)
        velocity_risk = self._check_velocity(user_id, user_history)
        risk_score += velocity_risk["score"]
        if velocity_risk["score"] > 0:
            risk_factors.append(velocity_risk["reason"])
        
        # Cap risk score at 100
        risk_score = min(risk_score, 100)
        
        # Determine fraud level
        if risk_score >= 80:
            fraud_level = "high"
            recommendation = "BLOCK_TRANSACTION"
        elif risk_score >= 50:
            fraud_level = "medium"
            recommendation = "REQUIRE_REVIEW"
        else:
            fraud_level = "low"
            recommendation = "ALLOW_TRANSACTION"
        
        return {
            "success": True,
            "risk_score": risk_score,
            "fraud_level": fraud_level,
            "risk_factors": risk_factors,
            "recommendation": recommendation,
            "requires_human_review": risk_score >= 50,
            "is_blocked": risk_score >= 80,
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_amount_anomaly(self, user_id: str, amount: float, history: Dict = None) -> Dict:
        """Check if amount is anomalous compared to user's history"""
        
        # Get user's average transaction amount
        avg_amount = self._get_user_average_amount(user_id, history)
        
        if avg_amount > 0 and amount > avg_amount * 3:
            return {"score": 40, "reason": f"Amount ${amount:,.2f} is 3x higher than average (${avg_amount:,.2f})"}
        elif avg_amount > 0 and amount > avg_amount * 2:
            return {"score": 20, "reason": f"Amount ${amount:,.2f} is 2x higher than average"}
        elif amount > 10000:
            return {"score": 30, "reason": f"Large transaction amount: ${amount:,.2f}"}
        
        return {"score": 0, "reason": ""}
    
    def _check_time_anomaly(self) -> Dict:
        """Check if transaction time is unusual (e.g., late night)"""
        current_hour = datetime.now().hour
        
        if 1 <= current_hour <= 4:
            return {"score": 25, "reason": f"Transaction at unusual hour: {current_hour}:00"}
        elif 5 <= current_hour <= 6 or 22 <= current_hour <= 23:
            return {"score": 10, "reason": f"Transaction at off-hour: {current_hour}:00"}
        
        return {"score": 0, "reason": ""}
    
    def _check_location_anomaly(self) -> Dict:
        """Check if transaction location is unusual (simulated)"""
        # In production, check against user's typical locations
        # For demo, randomly return a risk sometimes
        if random.random() < 0.1:  # 10% chance of location anomaly
            return {"score": 20, "reason": "Transaction from unusual location detected"}
        return {"score": 0, "reason": ""}
    
    def _check_recipient_risk(self, recipient: str) -> Dict:
        """Check if recipient is known to be risky"""
        high_risk_recipients = ["CRYPTO_EXCHANGE", "OFFSHORE_BANK", "UNKNOWN_OVERSEAS"]
        medium_risk_recipients = ["NEW_VENDOR", "INTERNATIONAL"]
        
        recipient_upper = recipient.upper()
        
        if any(risk in recipient_upper for risk in high_risk_recipients):
            return {"score": 35, "reason": f"High-risk recipient: {recipient}"}
        elif any(risk in recipient_upper for risk in medium_risk_recipients):
            return {"score": 15, "reason": f"Medium-risk recipient: {recipient}"}
        
        return {"score": 0, "reason": ""}
    
    def _check_velocity(self, user_id: str, history: Dict = None) -> Dict:
        """Check if user is making too many transactions too quickly"""
        # In production, check recent transaction count
        # For demo, return low risk
        return {"score": 0, "reason": ""}
    
    def _get_user_average_amount(self, user_id: str, history: Dict = None) -> float:
        """Get user's average transaction amount from history"""
        # In production, calculate from actual history
        # For demo, return a default value
        return 250.00


# Test
if __name__ == "__main__":
    tool = FraudDetectionTool()
    
    # Test large transaction
    result = tool.execute(user_id="user_123", amount=15000.00, recipient="CRYPTO_EXCHANGE")
    print(f"Fraud Detection Result:")
    print(f"  Risk Score: {result['risk_score']}/100")
    print(f"  Level: {result['fraud_level']}")
    print(f"  Recommendation: {result['recommendation']}")
    print(f"  Risk Factors: {', '.join(result['risk_factors'])}")