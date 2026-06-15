# memory/risk_memory.py
"""Track risk scores, fraud patterns, and suspicious activities per user"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json
import os
import hashlib


class RiskMemory:
    """
    Tracks risk scores and suspicious patterns across users.
    Used for fraud detection and compliance monitoring.
    """
    
    def __init__(self, persistence_dir: str = "data/risk_data"):
        """
        Initialize risk memory.
        
        Args:
            persistence_dir: Directory to store risk data
        """
        self.persistence_dir = persistence_dir
        os.makedirs(persistence_dir, exist_ok=True)
        
        # Risk profiles per user
        self.risk_profiles: Dict[str, Dict] = {}
        
        # Suspicious patterns (IP addresses, account numbers, etc.)
        self.blocklist: Dict[str, Dict] = {}
        
        # Recent alerts
        self.alerts: List[Dict] = []
        
        self._load_data()
    
    def record_action(self, user_id: str, action_type: str, details: Dict) -> Dict:
        """
        Record a user action and calculate risk score.
        
        Args:
            user_id: User identifier
            action_type: 'login', 'transfer', 'balance_check', 'profile_change'
            details: Action-specific details
            
        Returns:
            Risk assessment result
        """
        # Initialize profile if needed
        if user_id not in self.risk_profiles:
            self.risk_profiles[user_id] = self._create_risk_profile(user_id)
        
        profile = self.risk_profiles[user_id]
        timestamp = datetime.now()
        
        # Record the action
        action_record = {
            "type": action_type,
            "timestamp": timestamp.isoformat(),
            "details": details
        }
        
        profile["action_history"].append(action_record)
        
        # Keep only last 100 actions per user
        if len(profile["action_history"]) > 100:
            profile["action_history"] = profile["action_history"][-100:]
        
        # Calculate risk score for this action
        risk_assessment = self._assess_risk(user_id, action_type, details)
        
        # Update cumulative risk score
        old_risk = profile["current_risk_score"]
        profile["current_risk_score"] = min(100, old_risk + risk_assessment["increment"])
        
        # Decay risk over time (reduce by 10% if no recent violations)
        if self._has_no_recent_issues(user_id):
            profile["current_risk_score"] = max(0, profile["current_risk_score"] * 0.9)
        
        profile["last_updated"] = timestamp.isoformat()
        
        # Generate alert if risk is high
        if profile["current_risk_score"] >= 70:
            self._create_alert(user_id, "high_risk", profile["current_risk_score"])
        
        self._save_data()
        
        return {
            "risk_score": profile["current_risk_score"],
            "action_risk_increment": risk_assessment["increment"],
            "flags": risk_assessment["flags"],
            "requires_human_review": profile["current_risk_score"] >= 70
        }
    
    def check_transaction_risk(self, user_id: str, amount: float, 
                               recipient: str, transaction_type: str) -> Dict:
        """
        Specialized risk check for transactions.
        
        Args:
            user_id: User identifier
            amount: Transaction amount
            recipient: Recipient account number
            transaction_type: Type of transaction
            
        Returns:
            Risk assessment dictionary
        """
        risk_score = 0
        flags = []
        
        # Check amount-based risk
        if amount > 10000:
            risk_score += 40
            flags.append(f"large_transaction_${amount}")
        elif amount > 5000:
            risk_score += 20
            flags.append("moderate_transaction")
        
        # Check recipient reputation
        recipient_risk = self._check_recipient_risk(recipient)
        if recipient_risk > 0:
            risk_score += recipient_risk
            flags.append("suspicious_recipient")
        
        # Check user's recent velocity
        velocity = self._get_user_velocity(user_id)
        if velocity["daily_count"] > 10:
            risk_score += 30
            flags.append("high_velocity")
        elif velocity["hourly_count"] > 5:
            risk_score += 20
            flags.append("rapid_transactions")
        
        # Check if recipient is on blocklist
        if self.is_blocklisted("recipient", recipient):
            risk_score += 100
            flags.append("blocklisted_recipient")
        
        # Check if this is an unusual pattern
        if self._is_unusual_pattern(user_id, amount, recipient):
            risk_score += 25
            flags.append("unusual_pattern")
        
        risk_score = min(risk_score, 100)
        
        # Record this transaction for future risk analysis
        self.record_action(user_id, "transaction", {
            "amount": amount,
            "recipient": self._hash_sensitive_data(recipient),
            "type": transaction_type,
            "risk_score": risk_score,
            "flags": flags
        })
        
        return {
            "risk_score": risk_score,
            "flags": flags,
            "requires_review": risk_score >= 70,
            "is_blocked": risk_score >= 90
        }
    
    def add_to_blocklist(self, category: str, value: str, reason: str):
        """
        Add an item to the blocklist.
        
        Args:
            category: 'recipient', 'ip_address', 'device_id', 'user'
            value: The value to block
            reason: Why it's being blocked
        """
        key = self._hash_sensitive_data(value)
        
        self.blocklist[key] = {
            "category": category,
            "original_hash": key,
            "reason": reason,
            "added_at": datetime.now().isoformat(),
            "added_by": "system"
        }
        
        self._save_data()
        print(f"Added to blocklist: {category} - {reason}")
    
    def is_blocklisted(self, category: str, value: str) -> bool:
        """
        Check if a value is on the blocklist.
        
        Args:
            category: Category to check
            value: Value to check
            
        Returns:
            True if blocklisted
        """
        key = self._hash_sensitive_data(value)
        
        if key in self.blocklist:
            return self.blocklist[key]["category"] == category
        return False
    
    def get_risk_profile(self, user_id: str) -> Optional[Dict]:
        """Get complete risk profile for a user."""
        return self.risk_profiles.get(user_id)
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts within specified hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_iso = cutoff.isoformat()
        
        return [alert for alert in self.alerts if alert["timestamp"] > cutoff_iso]
    
    def reset_user_risk(self, user_id: str):
        """Reset risk score for a user (after review)."""
        if user_id in self.risk_profiles:
            self.risk_profiles[user_id]["current_risk_score"] = 0
            self.risk_profiles[user_id]["reset_at"] = datetime.now().isoformat()
            self._save_data()
    
    def _create_risk_profile(self, user_id: str) -> Dict:
        """Create a new risk profile for a user."""
        return {
            "user_id": user_id,
            "current_risk_score": 0,
            "action_history": [],
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_alerts": 0,
            "flags": []
        }
    
    def _assess_risk(self, user_id: str, action_type: str, details: Dict) -> Dict:
        """Assess risk for a specific action."""
        increment = 0
        flags = []
        
        if action_type == "login":
            # Check login from new device/location
            if details.get("is_new_device"):
                increment += 15
                flags.append("new_device_login")
            
            if details.get("unusual_hours"):
                increment += 10
                flags.append("unusual_hours")
        
        elif action_type == "transfer":
            amount = details.get("amount", 0)
            if amount > 5000:
                increment += 25
                flags.append("large_transfer")
            
            if details.get("new_recipient"):
                increment += 20
                flags.append("new_recipient")
        
        elif action_type == "profile_change":
            increment += 30
            flags.append("profile_change")
        
        elif action_type == "balance_check":
            # Multiple balance checks before transfer is suspicious
            recent_checks = self._count_recent_actions(user_id, "balance_check", minutes=10)
            if recent_checks > 3:
                increment += 10 * recent_checks
                flags.append("excessive_balance_checks")
        
        return {
            "increment": min(increment, 50),
            "flags": flags
        }
    
    def _check_recipient_risk(self, recipient: str) -> int:
        """Check if recipient has risk flags."""
        recipient_hash = self._hash_sensitive_data(recipient)
        
        # Check if recipient is known to be suspicious
        if recipient_hash in self.blocklist:
            return 50
        
        # Check if recipient appears in many failed transactions
        # (Simplified - would query database in production)
        return 0
    
    def _get_user_velocity(self, user_id: str) -> Dict:
        """Get transaction velocity for a user."""
        profile = self.risk_profiles.get(user_id, {})
        actions = profile.get("action_history", [])
        
        now = datetime.now()
        daily_count = 0
        hourly_count = 0
        
        for action in actions:
            action_time = datetime.fromisoformat(action["timestamp"])
            if action["type"] == "transaction":
                if (now - action_time).days == 0:
                    daily_count += 1
                if (now - action_time).seconds < 3600:
                    hourly_count += 1
        
        return {
            "daily_count": daily_count,
            "hourly_count": hourly_count
        }
    
    def _is_unusual_pattern(self, user_id: str, amount: float, recipient: str) -> bool:
        """Detect unusual transaction patterns."""
        profile = self.risk_profiles.get(user_id, {})
        actions = profile.get("action_history", [])
        
        # Check if user normally sends much smaller amounts
        recent_amounts = [
            a["details"].get("amount", 0) 
            for a in actions 
            if a["type"] == "transaction" and "amount" in a["details"]
        ]
        
        if recent_amounts:
            avg_amount = sum(recent_amounts) / len(recent_amounts)
            if amount > avg_amount * 3:  # 3x normal amount
                return True
        
        return False
    
    def _count_recent_actions(self, user_id: str, action_type: str, minutes: int = 10) -> int:
        """Count recent actions of a specific type."""
        profile = self.risk_profiles.get(user_id, {})
        actions = profile.get("action_history", [])
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        cutoff_iso = cutoff.isoformat()
        
        count = 0
        for action in actions:
            if action["type"] == action_type and action["timestamp"] > cutoff_iso:
                count += 1
        
        return count
    
    def _has_no_recent_issues(self, user_id: str, hours: int = 24) -> bool:
        """Check if user has had no risk issues recently."""
        profile = self.risk_profiles.get(user_id, {})
        actions = profile.get("action_history", [])
        
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_iso = cutoff.isoformat()
        
        for action in actions:
            if action["timestamp"] > cutoff_iso:
                for flag in action.get("details", {}).get("flags", []):
                    if "risk" in flag.lower():
                        return False
        
        return True
    
    def _create_alert(self, user_id: str, alert_type: str, risk_score: int):
        """Create a security alert."""
        alert = {
            "alert_id": hashlib.md5(f"{user_id}{datetime.now().isoformat()}".encode()).hexdigest()[:8],
            "user_id": user_id,
            "type": alert_type,
            "risk_score": risk_score,
            "timestamp": datetime.now().isoformat(),
            "resolved": False
        }
        
        self.alerts.append(alert)
        
        # Keep only last 1000 alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        # Update user profile
        if user_id in self.risk_profiles:
            self.risk_profiles[user_id]["total_alerts"] += 1
        
        self._save_data()
        
        # Print alert (in production, send to monitoring system)
        print(f"\n⚠️ RISK ALERT: User {user_id} - {alert_type} (Score: {risk_score})")
    
    def _hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for privacy."""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _save_data(self):
        """Save risk data to disk."""
        data = {
            "risk_profiles": self.risk_profiles,
            "blocklist": self.blocklist,
            "alerts": self.alerts[-100:]  # Save last 100 alerts
        }
        
        filepath = os.path.join(self.persistence_dir, "risk_data.json")
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving risk data: {e}")
    
    def _load_data(self):
        """Load risk data from disk."""
        filepath = os.path.join(self.persistence_dir, "risk_data.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                self.risk_profiles = data.get("risk_profiles", {})
                self.blocklist = data.get("blocklist", {})
                self.alerts = data.get("alerts", [])
            except Exception as e:
                print(f"Error loading risk data: {e}")
    
    def get_statistics(self) -> Dict:
        """Get risk memory statistics."""
        high_risk_users = sum(1 for p in self.risk_profiles.values() if p.get("current_risk_score", 0) >= 70)
        
        return {
            "total_users_tracked": len(self.risk_profiles),
            "high_risk_users": high_risk_users,
            "total_blocklist_entries": len(self.blocklist),
            "active_alerts": len([a for a in self.alerts if not a.get("resolved")]),
            "average_risk_score": sum(p.get("current_risk_score", 0) for p in self.risk_profiles.values()) / len(self.risk_profiles) if self.risk_profiles else 0
        }


# Test the risk memory
if __name__ == "__main__":
    print("="*60)
    print("Risk Memory Test")
    print("="*60)
    
    # Create risk memory
    risk_memory = RiskMemory(persistence_dir="data/test_risk")
    
    user_id = "test_user_001"
    
    # Test transaction risk check
    print("\nTransaction Risk Check ($15,000 to new recipient):")
    result = risk_memory.check_transaction_risk(
        user_id=user_id,
        amount=15000.00,
        recipient="NEW_ACCOUNT_999",
        transaction_type="wire_transfer"
    )
    
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # Add to blocklist
    print("\nAdding recipient to blocklist...")
    risk_memory.add_to_blocklist("recipient", "SCAM_ACCOUNT_123", "Reported for fraud")
    
    # Check if blocklisted
    print(f"Is blocklisted? {risk_memory.is_blocklisted('recipient', 'SCAM_ACCOUNT_123')}")
    
    # Get statistics
    print("\nRisk Memory Statistics:")
    stats = risk_memory.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Get recent alerts
    print("\nRecent Alerts:")
    for alert in risk_memory.get_recent_alerts():
        print(f"  {alert['type']} - User {alert['user_id']} (Score: {alert['risk_score']})")