# risk_checks/fraud_scorer.py
"""ML-based fraud probability scoring"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math
import random


@dataclass
class FraudScore:
    """Fraud score result"""
    total_score: float  # 0-100
    probability: float  # 0-1 probability of fraud
    risk_level: str  # low, medium, high, critical
    factors: List[Dict[str, Any]]
    recommendations: List[str]


class FraudScorer:
    """
    Machine learning inspired fraud scoring system.
    Calculates probability of fraud based on multiple factors.
    """
    
    def __init__(self):
        # Feature weights (trained weights in production)
        self.weights = {
            "amount_anomaly": 0.25,
            "velocity": 0.20,
            "location": 0.15,
            "device_risk": 0.10,
            "time_risk": 0.10,
            "recipient_risk": 0.15,
            "historical_fraud": 0.05,
        }
        
        # Fraud patterns database
        self.fraud_patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict:
        """Initialize known fraud patterns"""
        return {
            "rapid_successive_transfers": {"weight": 0.8, "threshold": 3},
            "amount_just_below_limit": {"weight": 0.6, "threshold": 1000},
            "new_device_transfer": {"weight": 0.7, "threshold": 1},
            "unusual_hours": {"weight": 0.5, "threshold": 1},
            "mismatched_location": {"weight": 0.9, "threshold": 1},
        }
    
    def calculate_fraud_score(self, transaction: Dict[str, Any], 
                              user_profile: Dict[str, Any],
                              user_history: List[Dict]) -> FraudScore:
        """
        Calculate comprehensive fraud score.
        
        Args:
            transaction: Current transaction details
            user_profile: User profile data
            user_history: User's transaction history
            
        Returns:
            FraudScore object with score and details
        """
        features = {}
        
        # Extract and score each feature
        features["amount_anomaly"] = self._score_amount_anomaly(transaction, user_history)
        features["velocity"] = self._score_velocity(transaction, user_history)
        features["location"] = self._score_location_risk(transaction, user_profile)
        features["device_risk"] = self._score_device_risk(transaction, user_profile)
        features["time_risk"] = self._score_time_risk(transaction)
        features["recipient_risk"] = self._score_recipient_risk(transaction, user_history)
        features["historical_fraud"] = self._score_historical_fraud(user_profile)
        
        # Calculate weighted total
        total_score = 0
        factors = []
        
        for feature_name, score in features.items():
            weight = self.weights.get(feature_name, 0.1)
            weighted_score = score * weight * 100
            total_score += weighted_score
            
            if score > 0.3:  # Only include significant factors
                factors.append({
                    "feature": feature_name,
                    "score": round(score, 2),
                    "weight": weight,
                    "weighted_score": round(weighted_score, 2),
                    "description": self._get_feature_description(feature_name, score)
                })
        
        # Cap at 100
        total_score = min(total_score, 100)
        
        # Calculate probability using sigmoid function
        probability = 1 / (1 + math.exp(-(total_score - 50) / 20))
        
        # Determine risk level
        if total_score >= 80:
            risk_level = "critical"
        elif total_score >= 60:
            risk_level = "high"
        elif total_score >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(total_score, factors)
        
        return FraudScore(
            total_score=round(total_score, 2),
            probability=round(probability, 3),
            risk_level=risk_level,
            factors=factors,
            recommendations=recommendations
        )
    
    def _score_amount_anomaly(self, transaction: Dict, history: List[Dict]) -> float:
        """Score amount anomaly (0-1, higher = more anomalous)"""
        amount = transaction.get("amount", 0)
        
        if not history:
            return 0.3 if amount > 10000 else 0.1
        
        # Calculate historical stats
        amounts = [tx.get("amount", 0) for tx in history[-50:] if tx.get("amount", 0) > 0]
        
        if not amounts:
            return 0.3 if amount > 10000 else 0.1
        
        mean_amount = sum(amounts) / len(amounts)
        std_amount = math.sqrt(sum((a - mean_amount) ** 2 for a in amounts) / len(amounts))
        
        if std_amount == 0:
            return 0.2
        
        # Z-score for amount
        z_score = abs(amount - mean_amount) / std_amount
        
        # Convert z-score to probability (0-1)
        if z_score >= 3:
            return 0.95
        elif z_score >= 2:
            return 0.8
        elif z_score >= 1:
            return 0.5
        else:
            return 0.2
    
    def _score_velocity(self, transaction: Dict, history: List[Dict]) -> float:
        """Score transaction velocity risk (0-1)"""
        if not history:
            return 0.1
        
        # Count transactions in last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_txs = [
            tx for tx in history[-20:]
            if tx.get("type") in ["transfer", "debit"]
        ]
        
        velocity_score = min(len(recent_txs) / 10, 1.0)
        
        return velocity_score
    
    def _score_location_risk(self, transaction: Dict, user_profile: Dict) -> float:
        """Score location-based risk (0-1)"""
        tx_location = transaction.get("location", "")
        user_location = user_profile.get("address", {}).get("city", "")
        
        # Simple location mismatch detection
        if tx_location and user_location and tx_location != user_location:
            return 0.7
        
        # Check for suspicious locations
        suspicious_locations = ["vpn", "proxy", "tor", "unknown"]
        if any(loc in tx_location.lower() for loc in suspicious_locations):
            return 0.9
        
        return 0.1
    
    def _score_device_risk(self, transaction: Dict, user_profile: Dict) -> float:
        """Score device-based risk (0-1)"""
        device_id = transaction.get("device_id", "")
        known_devices = user_profile.get("known_devices", [])
        
        if not device_id:
            return 0.3
        
        if device_id not in known_devices:
            return 0.6  # New device
        
        return 0.1
    
    def _score_time_risk(self, transaction: Dict) -> float:
        """Score time-based risk (0-1)"""
        tx_time = transaction.get("timestamp")
        if not tx_time:
            tx_time = datetime.now()
        elif isinstance(tx_time, str):
            tx_time = datetime.fromisoformat(tx_time)
        
        hour = tx_time.hour
        
        # High risk hours (1 AM - 4 AM)
        if 1 <= hour <= 4:
            return 0.8
        # Medium risk hours (11 PM - 1 AM, 4 AM - 6 AM)
        elif hour >= 23 or hour <= 6:
            return 0.5
        # Normal hours
        else:
            return 0.1
    
    def _score_recipient_risk(self, transaction: Dict, history: List[Dict]) -> float:
        """Score recipient-based risk (0-1)"""
        recipient = transaction.get("recipient", "").lower()
        
        # High risk keywords
        high_risk_keywords = ["crypto", "bitcoin", "casino", "gambling", "offshore"]
        for keyword in high_risk_keywords:
            if keyword in recipient:
                return 0.85
        
        # Check if recipient is new
        if history:
            known_recipients = set(tx.get("recipient", "") for tx in history[-50:])
            if recipient not in known_recipients:
                return 0.4
        
        return 0.1
    
    def _score_historical_fraud(self, user_profile: Dict) -> float:
        """Score based on historical fraud incidents"""
        fraud_count = user_profile.get("fraud_incidents", 0)
        
        if fraud_count >= 3:
            return 0.9
        elif fraud_count >= 1:
            return 0.5
        else:
            return 0.05
    
    def _get_feature_description(self, feature: str, score: float) -> str:
        """Get human-readable description for a feature"""
        descriptions = {
            "amount_anomaly": f"Transaction amount anomaly score: {score:.2f}",
            "velocity": f"Transaction velocity risk: {score:.2f}",
            "location": f"Location mismatch risk: {score:.2f}",
            "device_risk": f"Device risk score: {score:.2f}",
            "time_risk": f"Transaction time risk: {score:.2f}",
            "recipient_risk": f"Recipient risk score: {score:.2f}",
            "historical_fraud": f"Historical fraud score: {score:.2f}",
        }
        return descriptions.get(feature, f"Unknown feature: {score:.2f}")
    
    def _generate_recommendations(self, total_score: float, factors: List) -> List[str]:
        """Generate action recommendations based on score"""
        recommendations = []
        
        if total_score >= 80:
            recommendations.extend([
                "BLOCK TRANSACTION immediately",
                "Flag account for immediate review",
                "Contact customer via phone for verification",
                "File suspicious activity report"
            ])
        elif total_score >= 60:
            recommendations.extend([
                "Require additional authentication",
                "Place transaction on hold for review",
                "Send verification request to customer"
            ])
        elif total_score >= 30:
            recommendations.extend([
                "Monitor for similar patterns",
                "Request confirmation from customer",
                "Log for further analysis"
            ])
        else:
            recommendations.append("Allow transaction with standard monitoring")
        
        return recommendations


# Test
if __name__ == "__main__":
    print("="*60)
    print("FRAUD SCORER TEST")
    print("="*60)
    
    scorer = FraudScorer()
    
    # Test transaction
    test_transaction = {
        "amount": 25000.00,
        "recipient": "Crypto Exchange",
        "location": "Unknown",
        "device_id": "new_device_123",
        "timestamp": datetime.now().replace(hour=3, minute=0)
    }
    
    user_profile = {
        "address": {"city": "New York"},
        "known_devices": ["old_device_456"],
        "fraud_incidents": 0
    }
    
    user_history = [
        {"amount": 100, "type": "debit", "recipient": "Store A"},
        {"amount": 50, "type": "debit", "recipient": "Store B"},
        {"amount": 200, "type": "debit", "recipient": "Store C"},
    ]
    
    result = scorer.calculate_fraud_score(test_transaction, user_profile, user_history)
    
    print(f"\nFraud Score: {result.total_score}/100")
    print(f"Probability: {result.probability:.2%}")
    print(f"Risk Level: {result.risk_level}")
    print(f"\nFactors:")
    for factor in result.factors:
        print(f"  • {factor['feature']}: {factor['weighted_score']:.1f} pts - {factor['description']}")
    print(f"\nRecommendations:")
    for rec in result.recommendations:
        print(f"  • {rec}")