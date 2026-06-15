# data/__init__.py
"""Data module for persistent storage"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class DataManager:
    """Manager for all data operations"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.simulated_db_dir = self.data_dir / "simulated_db"
        self.fraud_logs_dir = self.data_dir / "fraud_logs"
        self.human_review_dir = self.data_dir / "human_review_queue"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create all necessary directories"""
        self.simulated_db_dir.mkdir(parents=True, exist_ok=True)
        self.fraud_logs_dir.mkdir(parents=True, exist_ok=True)
        self.human_review_dir.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # Account Operations
    # ========================================================================
    
    def get_accounts(self, user_id: Optional[str] = None) -> List[Dict]:
        """Get accounts for a user or all accounts"""
        accounts_file = self.simulated_db_dir / "accounts.json"
        
        if not accounts_file.exists():
            return []
        
        with open(accounts_file, 'r') as f:
            data = json.load(f)
        
        accounts = data.get("accounts", [])
        
        if user_id:
            return [acc for acc in accounts if acc.get("user_id") == user_id]
        
        return accounts
    
    def get_account_balance(self, user_id: str, account_type: str = "checking") -> float:
        """Get balance for a specific account"""
        accounts = self.get_accounts(user_id)
        
        for account in accounts:
            if account.get("account_type") == account_type:
                return account.get("balance", 0.0)
        
        return 0.0
    
    def update_account_balance(self, user_id: str, account_type: str, new_balance: float):
        """Update account balance"""
        accounts_file = self.simulated_db_dir / "accounts.json"
        
        with open(accounts_file, 'r') as f:
            data = json.load(f)
        
        for account in data["accounts"]:
            if account.get("user_id") == user_id and account.get("account_type") == account_type:
                account["balance"] = new_balance
                account["last_updated"] = datetime.now().isoformat()
                break
        
        data["summary"]["last_updated"] = datetime.now().isoformat()
        
        with open(accounts_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # ========================================================================
    # Transaction Operations
    # ========================================================================
    
    def add_transaction(self, transaction: Dict) -> str:
        """Add a new transaction"""
        transactions_file = self.simulated_db_dir / "transactions.json"
        
        with open(transactions_file, 'r') as f:
            data = json.load(f)
        
        # Generate transaction ID if not provided
        if "transaction_id" not in transaction:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            count = len(data["transactions"]) + 1
            transaction["transaction_id"] = f"TXN_{timestamp}_{count:03d}"
        
        transaction["timestamp"] = datetime.now().isoformat()
        data["transactions"].append(transaction)
        
        # Update summary
        data["summary"]["total_transactions"] = len(data["transactions"])
        data["summary"]["total_volume"] += transaction.get("amount", 0)
        data["summary"]["last_updated"] = datetime.now().isoformat()
        
        with open(transactions_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return transaction["transaction_id"]
    
    def get_transactions(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent transactions for a user"""
        transactions_file = self.simulated_db_dir / "transactions.json"
        
        if not transactions_file.exists():
            return []
        
        with open(transactions_file, 'r') as f:
            data = json.load(f)
        
        user_transactions = [
            t for t in data["transactions"] 
            if t.get("user_id") == user_id
        ]
        
        # Sort by timestamp (newest first)
        user_transactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return user_transactions[:limit]
    
    # ========================================================================
    # User Operations
    # ========================================================================
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        users_file = self.simulated_db_dir / "users.json"
        
        if not users_file.exists():
            return None
        
        with open(users_file, 'r') as f:
            data = json.load(f)
        
        for user in data["users"]:
            if user.get("user_id") == user_id:
                return user
        
        return None
    
    def update_user_limit(self, user_id: str, daily_limit: float = None, monthly_limit: float = None):
        """Update user transfer limits"""
        users_file = self.simulated_db_dir / "users.json"
        
        with open(users_file, 'r') as f:
            data = json.load(f)
        
        for user in data["users"]:
            if user.get("user_id") == user_id:
                if daily_limit:
                    user["daily_transfer_limit"] = daily_limit
                if monthly_limit:
                    user["monthly_transfer_limit"] = monthly_limit
                break
        
        with open(users_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # ========================================================================
    # Fraud Operations
    # ========================================================================
    
    def add_fraud_alert(self, alert: Dict) -> str:
        """Add a fraud alert"""
        alerts_file = self.fraud_logs_dir / "fraud_alerts.json"
        
        # Load existing alerts
        if alerts_file.exists():
            with open(alerts_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"alerts": [], "statistics": {
                "total_alerts": 0,
                "open_alerts": 0,
                "resolved_alerts": 0,
                "average_risk_score": 0,
                "by_severity": {"high": 0, "medium": 0, "low": 0},
                "last_updated": ""
            }}
        
        # Generate alert ID
        alert_id = f"FRD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        alert["alert_id"] = alert_id
        alert["timestamp"] = datetime.now().isoformat()
        alert["status"] = alert.get("status", "pending")
        
        data["alerts"].append(alert)
        
        # Update statistics
        data["statistics"]["total_alerts"] = len(data["alerts"])
        data["statistics"]["open_alerts"] = len([a for a in data["alerts"] if a.get("status") == "pending"])
        data["statistics"]["resolved_alerts"] = len([a for a in data["alerts"] if a.get("status") == "resolved"])
        
        # Update severity counts
        severity = alert.get("severity", "medium")
        data["statistics"]["by_severity"][severity] = data["statistics"]["by_severity"].get(severity, 0) + 1
        
        # Update average risk score
        total_risk = sum(a.get("risk_score", 0) for a in data["alerts"])
        data["statistics"]["average_risk_score"] = total_risk / len(data["alerts"]) if data["alerts"] else 0
        
        data["statistics"]["last_updated"] = datetime.now().isoformat()
        
        with open(alerts_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return alert_id
    
    def get_pending_alerts(self) -> List[Dict]:
        """Get all pending fraud alerts"""
        alerts_file = self.fraud_logs_dir / "fraud_alerts.json"
        
        if not alerts_file.exists():
            return []
        
        with open(alerts_file, 'r') as f:
            data = json.load(f)
        
        return [a for a in data["alerts"] if a.get("status") == "pending"]
    
    # ========================================================================
    # Human Review Operations
    # ========================================================================
    
    def add_review_request(self, review: Dict) -> str:
        """Add a human review request"""
        reviews_file = self.human_review_dir / "pending_reviews.json"
        
        if reviews_file.exists():
            with open(reviews_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"pending_reviews": [], "statistics": {
                "total_pending": 0,
                "total_in_review": 0,
                "total_approved": 0,
                "total_denied": 0,
                "average_wait_time_minutes": 0,
                "last_updated": ""
            }}
        
        # Generate review ID
        review_id = f"HRV_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        review["review_id"] = review_id
        review["submitted_at"] = datetime.now().isoformat()
        review["status"] = "pending"
        
        data["pending_reviews"].append(review)
        
        # Update statistics
        data["statistics"]["total_pending"] = len([r for r in data["pending_reviews"] if r.get("status") == "pending"])
        data["statistics"]["total_in_review"] = len([r for r in data["pending_reviews"] if r.get("status") == "in_review"])
        data["statistics"]["total_approved"] = len([r for r in data["pending_reviews"] if r.get("status") == "approved"])
        data["statistics"]["total_denied"] = len([r for r in data["pending_reviews"] if r.get("status") == "denied"])
        data["statistics"]["last_updated"] = datetime.now().isoformat()
        
        with open(reviews_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return review_id
    
    def update_review_status(self, review_id: str, status: str, approved_by: str = None, notes: str = None):
        """Update the status of a human review"""
        reviews_file = self.human_review_dir / "pending_reviews.json"
        
        if not reviews_file.exists():
            return
        
        with open(reviews_file, 'r') as f:
            data = json.load(f)
        
        for review in data["pending_reviews"]:
            if review.get("review_id") == review_id:
                review["status"] = status
                if approved_by:
                    review["approved_by"] = approved_by
                    review["approved_at"] = datetime.now().isoformat()
                if notes:
                    review["approval_notes"] = notes
                break
        
        # Update statistics
        data["statistics"]["total_pending"] = len([r for r in data["pending_reviews"] if r.get("status") == "pending"])
        data["statistics"]["total_in_review"] = len([r for r in data["pending_reviews"] if r.get("status") == "in_review"])
        data["statistics"]["total_approved"] = len([r for r in data["pending_reviews"] if r.get("status") == "approved"])
        data["statistics"]["total_denied"] = len([r for r in data["pending_reviews"] if r.get("status") == "denied"])
        data["statistics"]["