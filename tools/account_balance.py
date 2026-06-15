# tools/account_balance.py
from .base_tool import BaseTool
from typing import Dict, Any

class AccountBalanceTool(BaseTool):
    """Check account balance"""
    
    @property
    def name(self) -> str:
        return "get_account_balance"
    
    @property
    def description(self) -> str:
        return "Get the current balance for a user's checking or savings account"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "account_type": {
                    "type": "string",
                    "enum": ["checking", "savings"],
                    "description": "Type of account to check"
                },
                "user_id": {
                    "type": "string",
                    "description": "User identifier"
                }
            },
            "required": ["account_type", "user_id"]
        }
    
    def execute(self, account_type: str, user_id: str, **kwargs) -> Dict[str, Any]:
        # Simulated database lookup
        balances = {
            "user_123": {"checking": 5420.50, "savings": 15750.00}
        }
        
        balance = balances.get(user_id, {}).get(account_type, 0)
        
        return {
            "success": True,
            "account_type": account_type,
            "balance": balance,
            "currency": "USD"
        }