# tools/fund_transfer.py
"""Execute fund transfers between accounts"""

from tools.base_tool import BaseTool
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class FundTransferTool(BaseTool):
    """Execute internal and external fund transfers"""
    
    @property
    def name(self) -> str:
        return "execute_fund_transfer"
    
    @property
    def description(self) -> str:
        return "Transfer funds between accounts or to external recipients"
    
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
                    "description": "Amount to transfer"
                },
                "from_account": {
                    "type": "string",
                    "description": "Source account number",
                    "default": "checking"
                },
                "to_account": {
                    "type": "string",
                    "description": "Destination account number or recipient ID"
                },
                "description": {
                    "type": "string",
                    "description": "Transfer description/memo",
                    "default": ""
                }
            },
            "required": ["user_id", "amount", "to_account"]
        }
    
    def execute(self, user_id: str, amount: float, to_account: str, 
                from_account: str = "checking", description: str = "", **kwargs) -> Dict[str, Any]:
        """Execute the fund transfer"""
        
        # Validate amount
        if amount <= 0:
            return {
                "success": False,
                "error": "Transfer amount must be positive"
            }
        
        # Check sufficient balance (simulated)
        current_balance = self._get_balance(user_id, from_account)
        if current_balance < amount:
            return {
                "success": False,
                "error": f"Insufficient funds. Available: ${current_balance:,.2f}, Requested: ${amount:,.2f}"
            }
        
        # Execute transfer (simulated)
        transaction_id = str(uuid.uuid4())[:8].upper()
        
        return {
            "success": True,
            "transaction_id": f"TXN_{transaction_id}",
            "amount": amount,
            "from_account": from_account,
            "to_account": to_account,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "new_balance": current_balance - amount,
            "message": f"Successfully transferred ${amount:,.2f} to {to_account}"
        }
    
    def _get_balance(self, user_id: str, account: str) -> float:
        """Get current balance for an account (simulated)"""
        balances = {
            "user_123": {"checking": 5420.50, "savings": 15750.00},
            "test_user_001": {"checking": 15000.00, "savings": 50000.00},
        }
        return balances.get(user_id, {}).get(account, 10000.00)


# Test
if __name__ == "__main__":
    tool = FundTransferTool()
    result = tool.execute(
        user_id="test_user_001",
        amount=500.00,
        to_account="SAVINGS_001",
        description="Monthly savings"
    )
    print(f"Transfer result: {result['message']}")
    print(f"Transaction ID: {result.get('transaction_id', 'N/A')}")