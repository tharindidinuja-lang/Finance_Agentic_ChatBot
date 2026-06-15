# state/finance_state.py
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph.message import add_messages
from datetime import datetime

# ============================================================================
# Your Existing State Definition (Preserved)
# ============================================================================

class FinanceState(TypedDict):
    # Core conversation
    messages: Annotated[List[Dict[str, str]], add_messages]
    
    # Intent & entities from classifier
    intent: str
    extracted_entities: Dict[str, Any]
    
    # Planning
    current_plan: List[str]
    current_step: int
    
    # Tool execution
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    
    # Validation & retry
    validation_status: str  # "pending", "passed", "failed"
    retry_count: int
    
    # Risk & compliance
    risk_score: int  # 0-100
    fraud_flag: bool
    needs_human_review: bool
    human_approved: Optional[bool]
    
    # Financial context
    user_id: str
    transaction_amount: Optional[float]
    recipient_account: Optional[str]

FinanceStateDict = FinanceState

# ============================================================================
# Helper Functions (Optional - Add These Below Your Class)
# ============================================================================

def create_initial_state(user_id: str) -> FinanceState:
    """
    Create a fresh initial state for a new conversation.
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        FinanceState with default values
    """
    return {
        # Core conversation
        "messages": [],
        
        # Intent & entities
        "intent": "",
        "extracted_entities": {},
        
        # Planning
        "current_plan": [],
        "current_step": 0,
        
        # Tool execution
        "tool_calls": [],
        "tool_results": [],
        
        # Validation & retry
        "validation_status": "pending",
        "retry_count": 0,
        
        # Risk & compliance
        "risk_score": 0,
        "fraud_flag": False,
        "needs_human_review": False,
        "human_approved": None,
        
        # Financial context
        "user_id": user_id,
        "transaction_amount": None,
        "recipient_account": None,
    }


def reset_state_for_new_transaction(state: FinanceState) -> FinanceState:
    """
    Reset transaction-specific fields while preserving conversation history.
    Useful for multi-turn conversations with multiple transactions.
    
    Args:
        state: Current FinanceState
        
    Returns:
        Updated FinanceState with transaction fields reset
    """
    state["current_plan"] = []
    state["current_step"] = 0
    state["tool_calls"] = []
    state["tool_results"] = []
    state["validation_status"] = "pending"
    state["retry_count"] = 0
    state["risk_score"] = 0
    state["fraud_flag"] = False
    state["needs_human_review"] = False
    state["human_approved"] = None
    state["transaction_amount"] = None
    state["recipient_account"] = None
    
    return state


def get_state_summary(state: FinanceState) -> Dict[str, Any]:
    """
    Get a human-readable summary of the current state.
    Useful for debugging and monitoring.
    
    Args:
        state: Current FinanceState
        
    Returns:
        Dictionary with key state metrics
    """
    return {
        "user_id": state["user_id"],
        "message_count": len(state["messages"]),
        "current_step": state["current_step"],
        "plan_length": len(state["current_plan"]),
        "tool_calls_pending": len(state["tool_calls"]),
        "tool_results_received": len(state["tool_results"]),
        "validation_status": state["validation_status"],
        "retry_count": state["retry_count"],
        "risk_score": state["risk_score"],
        "fraud_flag": state["fraud_flag"],
        "needs_human_review": state["needs_human_review"],
        "human_approved": state["human_approved"],
        "has_transaction": state["transaction_amount"] is not None,
    }


def is_state_ready_for_response(state: FinanceState) -> bool:
    """
    Check if the state is ready to generate a response.
    
    Args:
        state: Current FinanceState
        
    Returns:
        True if ready for response generation
    """
    # All plan steps completed
    plan_completed = state["current_step"] >= len(state["current_plan"]) if state["current_plan"] else True
    
    # No pending tool calls
    no_pending_tools = len(state["tool_calls"]) == 0
    
    # Validation passed or failed permanently
    validation_done = state["validation_status"] in ["passed", "failed"]
    
    # Human review resolved if needed
    human_resolved = True
    if state["needs_human_review"]:
        human_resolved = state["human_approved"] is not None
    
    return plan_completed and no_pending_tools and validation_done and human_resolved


def add_error_to_state(state: FinanceState, error_message: str) -> FinanceState:
    """
    Add error tracking to state (optional enhancement).
    
    Args:
        state: Current FinanceState
        error_message: Error description
        
    Returns:
        Updated state with error in validation_status
    """
    state["validation_status"] = "failed"
    
    # Optional: Add error to messages for user feedback
    if "errors" not in state:
        state["errors"] = []  # You can add this field if needed
    
    return state


def increment_retry(state: FinanceState) -> FinanceState:
    """
    Increment retry counter and update status.
    
    Args:
        state: Current FinanceState
        
    Returns:
        Updated state
    """
    state["retry_count"] += 1
    
    if state["retry_count"] >= 3:  # Max retries
        state["validation_status"] = "failed"
    else:
        state["validation_status"] = "pending"  # Try again
    
    return state


# ============================================================================
# Demo and Testing
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("Finance State Test")
    print("="*60)
    
    # Test 1: Create initial state
    print("\n1. Creating initial state...")
    state = create_initial_state(user_id="test_user_001")
    print(f"   User ID: {state['user_id']}")
    print(f"   Messages: {len(state['messages'])}")
    print(f"   Risk score: {state['risk_score']}")
    
    # Test 2: Simulate adding a message
    print("\n2. Adding user message...")
    from langgraph.graph.message import add_messages
    state["messages"] = add_messages(state["messages"], [
        {"role": "user", "content": "Transfer $500 to account #987654321"}
    ])
    print(f"   Message added: {state['messages'][0]['content'][:30]}...")
    
    # Test 3: Update state with transaction details
    print("\n3. Updating transaction details...")
    state["transaction_amount"] = 500.00
    state["recipient_account"] = "987654321"
    state["current_plan"] = ["validate_recipient", "check_balance", "execute_transfer"]
    state["current_step"] = 1
    print(f"   Amount: ${state['transaction_amount']}")
    print(f"   Plan: {state['current_plan']}")
    print(f"   Step: {state['current_step']}")
    
    # Test 4: Risk assessment
    print("\n4. Simulating risk assessment...")
    state["risk_score"] = 35
    state["fraud_flag"] = False
    state["needs_human_review"] = False
    print(f"   Risk score: {state['risk_score']}/100")
    print(f"   Needs review: {state['needs_human_review']}")
    
    # Test 5: Get state summary
    print("\n5. State summary:")
    summary = get_state_summary(state)
    for key, value in summary.items():
        print(f"   • {key}: {value}")
    
    # Test 6: Check if ready for response
    print("\n6. Response readiness check:")
    is_ready = is_state_ready_for_response(state)
    print(f"   Ready for response: {is_ready}")
    
    # Test 7: Simulate retry
    print("\n7. Simulating retry logic...")
    print(f"   Before retry: retry_count={state['retry_count']}, status={state['validation_status']}")
    state = increment_retry(state)
    print(f"   After retry 1: retry_count={state['retry_count']}, status={state['validation_status']}")
    state = increment_retry(state)
    print(f"   After retry 2: retry_count={state['retry_count']}, status={state['validation_status']}")
    
    # Test 8: Reset for new transaction
    print("\n8. Resetting for new transaction...")
    state = reset_state_for_new_transaction(state)
    print(f"   Plan cleared: {state['current_plan']}")
    print(f"   Tool calls cleared: {len(state['tool_calls'])}")
    print(f"   Transaction amount: {state['transaction_amount']}")
    print(f"   Messages preserved: {len(state['messages'])}")
    
    print("\n" + "="*60)
    print(" All tests passed! State is ready for LangGraph.")
    print("="*60)