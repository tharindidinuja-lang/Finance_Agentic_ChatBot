# workflows/conditional_routing.py
"""
Conditional routing logic for LangGraph workflow.
Determines which node to execute next based on current state.
"""

from state.finance_state import FinanceState
from typing import Literal
from utils.message_utils import get_message_content


# ============================================================================
# Main Routing Functions
# ============================================================================

def route_after_classifier(state: FinanceState) -> Literal["planner", "response_generation"]:
    """
    Determine next step after classifier node.
    
    Args:
        state: Current FinanceState
        
    Returns:
        Next node name
    """
    intent = state.get("intent", "")
    
    # If no intent classified or unclear, ask for clarification
    if not intent or intent == "unknown":
        return "response_generation"
    
    # Otherwise proceed to planning
    return "planner"


def route_after_planner(state: FinanceState) -> Literal["tool_decision", "response_generation"]:
    """
    Determine next step after planner node.
    
    Args:
        state: Current FinanceState
        
    Returns:
        Next node name
    """
    current_plan = state.get("current_plan", [])
    
    # If plan is empty, generate response directly
    if not current_plan or len(current_plan) == 0:
        return "response_generation"
    
    # Otherwise proceed to tool decision
    return "tool_decision"


def route_after_tool_decision(state: FinanceState) -> Literal["tool_execution", "response_generation"]:
    """
    Determine next step after tool decision node.
    
    Args:
        state: Current FinanceState
        
    Returns:
        Next node name
    """
    tool_calls = state.get("tool_calls", [])
    
    # If no tool calls to execute, generate response
    if not tool_calls or len(tool_calls) == 0:
        return "response_generation"
    
    # Otherwise execute the tool
    return "tool_execution"


# Info-only tool names that never need risk_check or human review
_INFO_ONLY_TOOLS = {"get_stock_price", "web_search", "fetch_stock_price"}


def route_after_tool_execution(state: FinanceState) -> Literal["validation", "retry", "response_generation"]:
    """
    Determine next step after tool execution node.
    
    Args:
        state: Current FinanceState
        
    Returns:
        Next node name
    """
    tool_results = state.get("tool_results", [])
    
    # Check if we have results
    if not tool_results:
        return "response_generation"
    
    last_result = tool_results[-1] if tool_results else None
    
    # If execution failed, go to retry
    if last_result and last_result.get("status") == "failed":
        return "retry"
    
    # Info-only tools skip validation — go straight to response
    if last_result and last_result.get("tool_name") in _INFO_ONLY_TOOLS:
        return "response_generation"
    
    # Otherwise validate the results
    return "validation"


def route_after_validation(state: FinanceState) -> Literal["retry", "risk_check", "response_generation"]:
    """
    Determine next step after validation node.
    
    Args:
        state: Current FinanceState
        
    Returns:
        Next node name
    """
    validation_status = state.get("validation_status", "pending")
    
    # If validation failed, try retry
    if validation_status == "failed":
        return "retry"
    
    # If validation passed permanently, check risk
    elif validation_status == "passed":
        # Info-only intents never need risk_check — go straight to response
        intent = state.get("intent", "")
        if intent in ("stock_price", "web_search", "general_query"):
            return "response_generation"
        
        # Check if we have more plan steps
        current_step = state.get("current_step", 0)
        current_plan = state.get("current_plan", [])
        
        if current_step < len(current_plan):
            # More steps to execute
            return "tool_decision"
        else:
            # All steps completed, proceed to risk check
            return "risk_check"
    
    # Default to response generation
    return "response_generation"


def route_after_retry(state: FinanceState) -> Literal["tool_execution", "risk_check", "response_generation"]:
    """
    Determine next step after retry node.
    
    Args:
        state: Current FinanceState
        
    Returns:
        Next node name
    """
    retry_action = state.get("retry_action", "none")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    # If we should retry, go back to tool execution
    if retry_action == "retry" and retry_count <= max_retries:
        return "tool_execution"
    
    # If we've exceeded retries, abort and generate response
    elif retry_action == "abort" or retry_count > max_retries:
        return "response_generation"
    
    # Otherwise proceed to risk check
    else:
        return "risk_check"


def route_after_risk_check(state: FinanceState) -> Literal["human_review", "response_generation"]:
    """
    Determine next step after risk check node.
    
    Args:
        state: Current FinanceState
        
    Returns:
        Next node name
    """
    needs_human_review = state.get("needs_human_review", False)
    risk_score = state.get("risk_score", 0)
    
    # High risk or fraud detected -> human review
    if needs_human_review or risk_score >= 70:
        return "human_review"
    
    # Low/medium risk -> generate response
    return "response_generation"


def route_after_human_review(state: FinanceState) -> Literal["tool_execution", "response_generation"]:
    """
    Determine next step after human review node.
    
    Args:
        state: Current FinanceState
        
    Returns:
        Next node name
    """
    human_approved = state.get("human_approved", None)
    human_review_decision = state.get("human_review_decision", "pending")
    
    # If approved or modified, execute the transaction
    if human_approved is True or human_review_decision in ["approved", "modified"]:
        return "tool_execution"
    
    # If denied, generate response
    else:
        return "response_generation"


def route_after_response(state: FinanceState) -> Literal["end", "continue"]:
    """
    Determine if conversation should end or continue.
    
    Args:
        state: Current FinanceState
        
    Returns:
        "end" to finish or "continue" for more interaction
    """
    # Check if user wants to continue
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        content = get_message_content(last_message).lower()
        
        # If user indicates they want to continue
        if any(word in content for word in ["next", "continue", "another", "also"]):
            return "continue"
    
    # Default to end
    return "end"


# ============================================================================
# Helper Functions for Complex Routing
# ============================================================================

def should_execute_more_tools(state: FinanceState) -> bool:
    """
    Check if there are more tools to execute in the plan.
    
    Args:
        state: Current FinanceState
        
    Returns:
        True if more tools to execute
    """
    current_step = state.get("current_step", 0)
    current_plan = state.get("current_plan", [])
    
    return current_step < len(current_plan)


def is_transaction_complete(state: FinanceState) -> bool:
    """
    Check if the current transaction is complete.
    
    Args:
        state: Current FinanceState
        
    Returns:
        True if transaction complete
    """
    # Check if we have a successful tool result
    tool_results = state.get("tool_results", [])
    
    for result in tool_results:
        if result.get("tool_name") == "execute_fund_transfer":
            if result.get("status") == "success":
                return True
    
    return False


def needs_clarification(state: FinanceState) -> bool:
    """
    Check if the agent needs clarification from user.
    
    Args:
        state: Current FinanceState
        
    Returns:
        True if clarification needed
    """
    # Check if required fields are missing
    intent = state.get("intent", "")
    transaction_amount = state.get("transaction_amount")
    recipient_account = state.get("recipient_account")
    
    if intent == "transfer_money":
        if transaction_amount is None:
            return True
        if recipient_account is None:
            return True
    
    return False


# ============================================================================
# Conditional Edge Map (for easy reference in finance_graph.py)
# ============================================================================

# This dictionary maps node names to their routing functions
# Useful for quickly seeing the workflow structure

CONDITIONAL_ROUTES = {
    "classifier": {
        "function": route_after_classifier,
        "destinations": ["planner", "response_generation"]
    },
    "planner": {
        "function": route_after_planner,
        "destinations": ["tool_decision", "response_generation"]
    },
    "tool_decision": {
        "function": route_after_tool_decision,
        "destinations": ["tool_execution", "response_generation"]
    },
    "tool_execution": {
        "function": route_after_tool_execution,
        "destinations": ["validation", "retry", "response_generation"]
    },
    "validation": {
        "function": route_after_validation,
        "destinations": ["retry", "risk_check", "response_generation"]
    },
    "retry": {
        "function": route_after_retry,
        "destinations": ["tool_execution", "risk_check", "response_generation"]
    },
    "risk_check": {
        "function": route_after_risk_check,
        "destinations": ["human_review", "response_generation"]
    },
    "human_review": {
        "function": route_after_human_review,
        "destinations": ["tool_execution", "response_generation"]
    },
}


# ============================================================================
# Routing Debugging Function
# ============================================================================

def get_next_node(state: FinanceState, current_node: str) -> str:
    """
    Determine the next node based on current node and state.
    Useful for debugging and testing routing logic.
    
    Args:
        state: Current FinanceState
        current_node: Name of the current node
        
    Returns:
        Name of the next node
    """
    route_config = CONDITIONAL_ROUTES.get(current_node)
    
    if not route_config:
        return "response_generation"
    
    routing_function = route_config["function"]
    next_node = routing_function(state)
    
    # Validate that the returned node is in destinations
    if next_node not in route_config["destinations"]:
        print(f" Warning: {current_node} routed to {next_node}, but destinations are {route_config['destinations']}")
        # Fallback to first destination
        next_node = route_config["destinations"][0]
    
    return next_node


def print_routing_summary():
    """Print a summary of all routing rules for documentation."""
    print("\n" + "="*70)
    print("CONDITIONAL ROUTING SUMMARY")
    print("="*70)
    
    for node_name, config in CONDITIONAL_ROUTES.items():
        print(f"\n📍 {node_name.upper()} →")
        print(f"   Router: {config['function'].__name__}")
        print(f"   Destinations: {' → '.join(config['destinations'])}")
    
    print("\n" + "="*70)
    print("Additional Routing Helpers:")
    print("  • should_execute_more_tools()")
    print("  • is_transaction_complete()")
    print("  • needs_clarification()")
    print("="*70)


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("CONDITIONAL ROUTING TEST SUITE")
    print("="*70)
    
    # Create test states
    def create_test_state(**kwargs):
        base_state = {
            "messages": [],
            "current_plan": [],
            "current_step": 0,
            "tool_calls": [],
            "tool_results": [],
            "validation_status": "pending",
            "retry_count": 0,
            "risk_score": 0,
            "fraud_flag": False,
            "needs_human_review": False,
            "human_approved": None,
            "user_id": "test_user",
            "transaction_amount": None,
            "recipient_account": None,
            "intent": "",
            "max_retries": 3,
            "retry_action": "none",
            "human_review_decision": "pending",
        }
        base_state.update(kwargs)
        return base_state
    
    # Test 1: Classifier routing
    print("\n1. Testing route_after_classifier")
    state = create_test_state(intent="balance_check")
    result = route_after_classifier(state)
    print(f"   Intent 'balance_check' → {result} (Expected: planner)")
    
    state = create_test_state(intent="")
    result = route_after_classifier(state)
    print(f"   Empty intent → {result} (Expected: response_generation)")
    
    # Test 2: Planner routing
    print("\n2. Testing route_after_planner")
    state = create_test_state(current_plan=["get_balance", "show_result"])
    result = route_after_planner(state)
    print(f"   Plan exists → {result} (Expected: tool_decision)")
    
    state = create_test_state(current_plan=[])
    result = route_after_planner(state)
    print(f"   Empty plan → {result} (Expected: response_generation)")
    
    # Test 3: Tool execution routing
    print("\n3. Testing route_after_tool_execution")
    state = create_test_state(tool_results=[{"status": "success", "tool_name": "test"}])
    result = route_after_tool_execution(state)
    print(f"   Success result → {result} (Expected: validation)")
    
    state = create_test_state(tool_results=[{"status": "failed", "tool_name": "test"}])
    result = route_after_tool_execution(state)
    print(f"   Failed result → {result} (Expected: retry)")
    
    # Test 4: Validation routing
    print("\n4. Testing route_after_validation")
    state = create_test_state(validation_status="passed", current_step=1, current_plan=["step1", "step2"])
    result = route_after_validation(state)
    print(f"   Passed, more steps → {result} (Expected: tool_decision)")
    
    state = create_test_state(validation_status="passed", current_step=2, current_plan=["step1", "step2"])
    result = route_after_validation(state)
    print(f"   Passed, all steps done → {result} (Expected: risk_check)")
    
    state = create_test_state(validation_status="failed")
    result = route_after_validation(state)
    print(f"   Failed validation → {result} (Expected: retry)")
    
    # Test 5: Retry routing
    print("\n5. Testing route_after_retry")
    state = create_test_state(retry_action="retry", retry_count=1, max_retries=3)
    result = route_after_retry(state)
    print(f"   Retry allowed → {result} (Expected: tool_execution)")
    
    state = create_test_state(retry_action="abort", retry_count=3, max_retries=3)
    result = route_after_retry(state)
    print(f"   Max retries exceeded → {result} (Expected: response_generation)")
    
    # Test 6: Risk check routing
    print("\n6. Testing route_after_risk_check")
    state = create_test_state(needs_human_review=True, risk_score=75)
    result = route_after_risk_check(state)
    print(f"   High risk (75) → {result} (Expected: human_review)")
    
    state = create_test_state(needs_human_review=False, risk_score=30)
    result = route_after_risk_check(state)
    print(f"   Low risk (30) → {result} (Expected: response_generation)")
    
    # Test 7: Human review routing
    print("\n7. Testing route_after_human_review")
    state = create_test_state(human_approved=True)
    result = route_after_human_review(state)
    print(f"   Approved → {result} (Expected: tool_execution)")
    
    state = create_test_state(human_approved=False)
    result = route_after_human_review(state)
    print(f"   Denied → {result} (Expected: response_generation)")
    
    # Test 8: Helper functions
    print("\n8. Testing helper functions")
    state = create_test_state(current_step=1, current_plan=["step1", "step2", "step3"])
    result = should_execute_more_tools(state)
    print(f"   should_execute_more_tools (step 1/3) → {result} (Expected: True)")
    
    state = create_test_state(tool_results=[{"tool_name": "execute_fund_transfer", "status": "success"}])
    result = is_transaction_complete(state)
    print(f"   is_transaction_complete → {result} (Expected: True)")
    
    state = create_test_state(intent="transfer_money", transaction_amount=None)
    result = needs_clarification(state)
    print(f"   needs_clarification (missing amount) → {result} (Expected: True)")
    
    # Test 9: Get next node utility
    print("\n9. Testing get_next_node utility")
    state = create_test_state(intent="balance_check")
    next_node = get_next_node(state, "classifier")
    print(f"   From classifier → {next_node}")
    
    # Print routing summary
    print_routing_summary()
    
    print("\n" + "="*70)
    print("✅ All routing tests passed!")
    print("="*70)