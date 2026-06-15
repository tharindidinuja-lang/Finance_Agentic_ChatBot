# nodes/retry_node.py
from state.finance_state import FinanceState
from config.constants import MAX_RETRY_ATTEMPTS, RETRY_BACKOFF_SECONDS
import time

def retry_node(state: FinanceState) -> FinanceState:
    """
    Handle retry logic for failed operations.
    Increments retry count and determines if we should retry or give up.
    """
    
    current_retry = state.get("retry_count", 0)
    validation_status = state.get("validation_status", "")
    
    # Only retry if validation failed and we haven't exceeded max retries
    if validation_status == "failed" and current_retry < MAX_RETRY_ATTEMPTS:
        # Increment retry count
        state["retry_count"] = current_retry + 1
        
        # Add backoff delay (exponential)
        backoff_seconds = RETRY_BACKOFF_SECONDS[min(current_retry, len(RETRY_BACKOFF_SECONDS)-1)]
        time.sleep(backoff_seconds)
        
        # Reset validation status for retry
        state["validation_status"] = "pending"
        
        # Clear the failed tool result so we can try again
        if state["tool_results"] and state["tool_results"][-1]["status"] == "failed":
            state["tool_results"].pop()
        
        # Re-add the failed tool call
        if state["tool_calls"]:
            # Tool call is already there, just need to re-execute
            pass
        
        state["retry_action"] = "retry"
        state["retry_message"] = f"Retry attempt {state['retry_count']} of {MAX_RETRY_ATTEMPTS}"
        
    elif validation_status == "failed" and current_retry >= MAX_RETRY_ATTEMPTS:
        # Max retries exceeded - give up
        state["retry_action"] = "abort"
        state["retry_message"] = f"Max retries ({MAX_RETRY_ATTEMPTS}) exceeded. Operation failed."
        state["validation_status"] = "failed_permanent"
        
    else:
        # No retry needed
        state["retry_action"] = "none"
        state["retry_message"] = ""
    
    return state

# Conditional edge function for LangGraph routing
def should_retry(state: FinanceState) -> str:
    """Determine next step after retry node"""
    
    action = state.get("retry_action", "none")
    
    if action == "retry":
        return "tool_execution"  # Go back to execute the tool again
    elif action == "abort":
        return "response_generation"  # Generate error response
    else:
        return "risk_check"  # Move to next step (risk check)

if __name__ == "__main__":
    # Test retry scenario
    test_state = {
        "validation_status": "failed",
        "retry_count": 0,
        "tool_results": [{"status": "failed", "error": "API timeout"}],
        "tool_calls": [{"tool_name": "fetch_stock_price"}]
    }
    
    result = retry_node(test_state)
    print(f"Retry action: {result['retry_action']}")
    print(f"Retry count: {result['retry_count']}")
    print(f"Message: {result['retry_message']}")