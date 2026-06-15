# nodes/tool_execution_node.py
from state.finance_state import FinanceState
from nodes.tool_decision_node import ToolRegistry
from typing import Dict, Any
import time

def tool_execution_node(state: FinanceState) -> FinanceState:
    """
    Execute the pending tool call.
    Handles success/failure and stores results.
    """
    
    if not state["tool_calls"]:
        # No tool to execute
        return state
    
    # Get the most recent pending tool call
    pending_call = state["tool_calls"][-1]
    tool_name = pending_call["tool_name"]
    params = pending_call["parameters"]
    
    registry = ToolRegistry()
    tool = registry.get_tool(tool_name)
    
    try:
        # Execute the tool
        if hasattr(tool, 'execute'):
            # Tool is a class instance
            result = tool.execute(**params)
        else:
            # Tool is a function
            result = tool(**params)
        
        # Store successful result
        state["tool_results"].append({
            "tool_name": tool_name,
            "status": "success",
            "result": result,
            "timestamp": time.time()
        })
        
        # Move to next step
        state["current_step"] += 1
        state["validation_status"] = "passed"
        
    except Exception as e:
        # Store failure
        state["tool_results"].append({
            "tool_name": tool_name,
            "status": "failed",
            "error": str(e),
            "timestamp": time.time()
        })
        state["validation_status"] = "failed"
    
    # Clear executed tool call
    state["tool_calls"].pop()
    
    return state

if __name__ == "__main__":
    # Test with a balance check
    test_state = {
        "messages": [{"role": "user", "content": "What's my balance?"}],
        "current_plan": ["get_account_balance"],
        "current_step": 0,
        "tool_calls": [{
            "tool_name": "get_account_balance",
            "parameters": {"account_type": "checking", "user_id": "user_123"},
            "step_index": 0
        }],
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
    
    result = tool_execution_node(test_state)
    print(f"Execution result: {result['tool_results'][0]}")