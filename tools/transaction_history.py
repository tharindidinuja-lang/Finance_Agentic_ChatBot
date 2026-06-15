# tools/transaction_history.py
"""Fetch and analyze transaction history"""

from tools.base_tool import BaseTool
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
import os


class TransactionHistoryTool(BaseTool):
    """Get transaction history for a user"""
    
    @property
    def name(self) -> str:
        return "get_transaction_history"
    
    @property
    def description(self) -> str:
        return "Get recent transaction history for a user's account"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back (default 30)",
                    "default": 30
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of transactions to return",
                    "default": 10
                },
                "transaction_type": {
                    "type": "string",
                    "enum": ["all", "debit", "credit", "transfer"],
                    "description": "Filter by transaction type",
                    "default": "all"
                }
            },
            "required": ["user_id"]
        }
    
    def execute(self, user_id: str, days: int = 30, limit: int = 10, 
                transaction_type: str = "all", **kwargs) -> Dict[str, Any]:
        """Fetch transaction history"""
        
        # Simulated transaction database
        transactions = self._get_simulated_transactions(user_id, days)
        
        # Filter by type
        if transaction_type != "all":
            transactions = [t for t in transactions if t.get("type") == transaction_type]
        
        # Sort by date (newest first)
        transactions.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        # Limit results
        transactions = transactions[:limit]
        
        # Calculate summary
        total_debits = sum(t.get("amount", 0) for t in transactions if t.get("type") == "debit")
        total_credits = sum(t.get("amount", 0) for t in transactions if t.get("type") == "credit")
        
        return {
            "success": True,
            "user_id": user_id,
            "transaction_count": len(transactions),
            "transactions": transactions,
            "summary": {
                "total_debits": total_debits,
                "total_credits": total_credits,
                "net_change": total_credits - total_debits,
                "period_days": days
            }
        }
    
    def _get_simulated_transactions(self, user_id: str, days: int) -> List[Dict]:
        """Generate simulated transaction data"""
        
        # In production, this would query a real database
        # For demo, return sample data
        
        sample_transactions = [
            {
                "id": "TXN001",
                "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "description": "Grocery Store",
                "amount": 156.32,
                "type": "debit",
                "category": "food",
                "status": "completed"
            },
            {
                "id": "TXN002", 
                "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "description": "Salary Deposit",
                "amount": 4500.00,
                "type": "credit",
                "category": "income",
                "status": "completed"
            },
            {
                "id": "TXN003",
                "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                "description": "Netflix Subscription",
                "amount": 15.99,
                "type": "debit",
                "category": "entertainment",
                "status": "completed"
            },
            {
                "id": "TXN004",
                "date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "description": "Transfer to Savings",
                "amount": 500.00,
                "type": "transfer",
                "category": "savings",
                "status": "completed"
            },
            {
                "id": "TXN005",
                "date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
                "description": "Restaurant",
                "amount": 78.45,
                "type": "debit",
                "category": "food",
                "status": "completed"
            },
            {
                "id": "TXN006",
                "date": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
                "description": "Electric Bill",
                "amount": 125.00,
                "type": "debit",
                "category": "utilities",
                "status": "completed"
            },
            {
                "id": "TXN007",
                "date": (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d"),
                "description": "Amazon Purchase",
                "amount": 89.99,
                "type": "debit",
                "category": "shopping",
                "status": "completed"
            }
        ]
        
        # Filter by days
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered = []
        
        for tx in sample_transactions:
            tx_date = datetime.strptime(tx["date"], "%Y-%m-%d")
            if tx_date >= cutoff_date:
                filtered.append(tx)
        
        return filtered


# Test
if __name__ == "__main__":
    tool = TransactionHistoryTool()
    result = tool.execute(user_id="user_123", days=30, limit=5)
    print(f"Transactions found: {result['transaction_count']}")
    for tx in result['transactions']:
        print(f"  ${tx['amount']} - {tx['description']}")