# nodes/tool_decision_node.py
from state.finance_state import FinanceState
from typing import Dict, Any, List
from utils.message_utils import get_message_content

# Import all available tools
from tools.account_balance import AccountBalanceTool
from tools.fund_transfer import FundTransferTool
from tools.stock_price import StockPriceTool
from tools.transaction_history import TransactionHistoryTool
from tools.web_search import WebSearchTool, RealTimeStockTool

class ToolRegistry:
    """Registry of all available tools"""
    
    def __init__(self):
        self.tools = {
            "get_account_balance": AccountBalanceTool(),
            "execute_fund_transfer": FundTransferTool(),
            "fetch_stock_price": StockPriceTool(),
            "get_transaction_history": TransactionHistoryTool(),
            "validate_recipient_account": self.validate_account,  # Simple function
            "check_sufficient_balance": self.check_balance,
            "log_transaction": self.log_transaction,
            "run_fraud_detection": self.run_fraud_detection,
            "web_search": WebSearchTool(),
            "get_stock_price": RealTimeStockTool()
        }
    
    def validate_account(self, account_number: str, **kwargs) -> Dict[str, Any]:
        """Validate if recipient account exists"""
        # Simulated validation
        valid_accounts = ["987654321", "123456789", "555555555"]
        return {
            "success": account_number in valid_accounts,
            "account_number": account_number,
            "message": "Valid account" if account_number in valid_accounts else "Invalid account"
        }
    
    def check_balance(self, amount: float, user_id: str, **kwargs) -> Dict[str, Any]:
        """Check if user has sufficient balance"""
        # Simulated balance check
        user_balance = 15000.0  # Demo balance
        return {
            "success": user_balance >= amount,
            "current_balance": user_balance,
            "requested_amount": amount,
            "sufficient": user_balance >= amount
        }
    
    def log_transaction(self, **kwargs) -> Dict[str, Any]:
        """Log transaction for audit"""
        return {"success": True, "logged": True}
    
    def run_fraud_detection(self, transactions: List, **kwargs) -> Dict[str, Any]:
        """Run fraud detection model"""
        # Simulated fraud check
        return {
            "fraud_score": 15,  # 0-100, lower is better
            "is_suspicious": False,
            "flags": []
        }
    
    def get_tool(self, tool_name: str):
        """Get tool by name"""
        return self.tools.get(tool_name)

def tool_decision_node(state: FinanceState) -> FinanceState:
    """
    Determine which specific tool to call for the current plan step.
    Also extract parameters from the conversation.
    """
    
    registry = ToolRegistry()
    current_step_index = state["current_step"]
    plan = state["current_plan"]
    
    if current_step_index >= len(plan):
        # No more steps
        return state
    
    next_tool_name = plan[current_step_index]
    tool = registry.get_tool(next_tool_name)
    
    if tool is None:
        # Tool not found
        state["validation_status"] = "failed"
        return state
    
    # Extract parameters based on tool type
    params = extract_parameters(state, next_tool_name)
    
    # Prepare tool call
    tool_call = {
        "tool_name": next_tool_name,
        "parameters": params,
        "step_index": current_step_index
    }
    
    state["tool_calls"].append(tool_call)
    
    return state

def extract_parameters(state: FinanceState, tool_name: str) -> Dict[str, Any]:
    """Extract parameters from conversation and state"""
    
    params = {"user_id": state["user_id"]}
    last_message = get_message_content(state["messages"][-1]) if state.get("messages") else ""
    last_message_lower = last_message.lower()
    
    if tool_name == "get_account_balance":
        if "savings" in last_message_lower:
            params["account_type"] = "savings"
        else:
            params["account_type"] = "checking"
    
    elif tool_name in ["execute_fund_transfer", "validate_recipient_account"]:
        # Extract amount and recipient
        import re
        amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)', last_message_lower)
        if amount_match:
            params["amount"] = float(amount_match.group(1))
            state["transaction_amount"] = params["amount"]
        
        account_match = re.search(r'account #?(\d+)', last_message_lower)
        if account_match:
            params["recipient_account"] = account_match.group(1)
            state["recipient_account"] = params["recipient_account"]
            
    elif tool_name == "web_search":
        params["query"] = last_message
    
    elif tool_name in ["fetch_stock_price", "get_stock_price"]:
        # Extract stock symbol
        stock_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        for symbol in stock_symbols:
            if symbol.lower() in last_message_lower:
                params["symbol"] = symbol
                break
        else:
            # Try to extract the word before "stock" or "price"
            import re
            match = re.search(r'(\w+)\s+(?:stock|price)', last_message_lower)
            if match:
                params["company"] = match.group(1)
                params["symbol"] = match.group(1).upper()
            else:
                params["symbol"] = "AAPL"  # Default
    
    return params

if __name__ == "__main__":
    test_state = {
        "messages": [{"role": "user", "content": "Transfer $500 to account #987654321"}],
        "current_plan": ["validate_recipient_account", "check_sufficient_balance", "execute_fund_transfer"],
        "current_step": 0,
        "tool_calls": [],
        "tool_results": [],
        "validation_status": "pending",
        "retry_count": 0,
        "risk_score": 0,
        "fraud_flag": False,
        "needs_human_review": False,
        "human_approved": None,
        "user_id": "user_123",
        "transaction_amount": None,
        "recipient_account": None
    }
    
    result = tool_decision_node(test_state)
    print(f"Tool call created: {result['tool_calls'][0]}")