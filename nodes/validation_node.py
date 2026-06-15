# nodes/validation_node.py
from state.finance_state import FinanceState
from typing import Dict, Any

def validation_node(state: FinanceState) -> FinanceState:
    """
    Validate tool execution results.
    Check for data integrity, unexpected values, and business rule violations.
    """
    
    if not state["tool_results"]:
        state["validation_status"] = "failed"
        state["validation_message"] = "No tool results to validate"
        return state
    
    last_result = state["tool_results"][-1]
    
    if last_result["status"] == "failed":
        state["validation_status"] = "failed"
        state["validation_message"] = f"Tool execution failed: {last_result.get('error', 'Unknown error')}"
        return state
    
    result_data = last_result["result"]
    tool_name = last_result["tool_name"]
    
    # Tool-specific validation
    if tool_name == "get_account_balance":
        valid = validate_balance_result(result_data)
        
    elif tool_name == "execute_fund_transfer":
        valid = validate_transfer_result(result_data, state)
        
    elif tool_name in ["fetch_stock_price", "get_stock_price"]:
        valid = validate_stock_result(result_data)
        
    else:
        # Default validation: check for success flag
        valid = result_data.get("success", True)
    
    if valid:
        state["validation_status"] = "passed"
        state["validation_message"] = "Validation passed"
    else:
        state["validation_status"] = "failed"
        state["validation_message"] = f"Validation failed for {tool_name}"
    
    return state

def validate_balance_result(result: Dict[str, Any]) -> bool:
    """Validate balance result"""
    required_fields = ["balance", "account_type"]
    for field in required_fields:
        if field not in result:
            return False
    
    # Balance should be non-negative
    if result.get("balance", -1) < 0:
        return False
    
    return True

def validate_transfer_result(result: Dict[str, Any], state: FinanceState) -> bool:
    """Validate transfer result"""
    # Check if transfer amount is within limits
    from config.constants import MAX_SINGLE_TRANSFER
    
    amount = state.get("transaction_amount", 0)
    if amount > MAX_SINGLE_TRANSFER:
        return False
    
    # Check for success flag
    if not result.get("success", False):
        return False
    
    return True

def validate_stock_result(result: Dict[str, Any]) -> bool:
    """Validate stock price result"""
    if "price_info" in result:
        return True
    # Price should be a positive number
    price = result.get("price", 0)
    if not isinstance(price, (int, float)) or price <= 0:
        return False
    
    return True

if __name__ == "__main__":
    test_state = {
        "tool_results": [{
            "tool_name": "get_account_balance",
            "status": "success",
            "result": {"balance": 5420.50, "account_type": "checking", "success": True}
        }],
        "validation_status": "pending",
        "validation_message": "",
        "transaction_amount": None,
        "user_id": "user_123"
    }
    
    result = validation_node(test_state)
    print(f"Validation status: {result['validation_status']}")
    print(f"Message: {result['validation_message']}")