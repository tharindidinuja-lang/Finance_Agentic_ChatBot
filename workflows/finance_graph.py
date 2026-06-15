# workflows/finance_graph.py
from langgraph.graph import StateGraph, END

from state.finance_state import FinanceState
from nodes.classifier_node import classifier_node
from nodes.planner_node import planner_node
from nodes.tool_decision_node import tool_decision_node
from nodes.tool_execution_node import tool_execution_node
from nodes.validation_node import validation_node
from nodes.retry_node import retry_node
from nodes.risk_check_node import risk_check_node
from nodes.human_review_node import human_review_node
from nodes.response_generation_node import response_generation_node
from workflows.conditional_routing import (
    route_after_classifier,
    route_after_planner,
    route_after_tool_decision,
    route_after_tool_execution,
    route_after_validation,
    route_after_retry,
    route_after_risk_check,
    route_after_human_review,
)


def create_finance_graph():
    """Create and compile the complete LangGraph finance workflow."""

    workflow = StateGraph(FinanceState)

    # Add all nodes
    workflow.add_node("classifier", classifier_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("tool_decision", tool_decision_node)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("retry", retry_node)
    workflow.add_node("risk_check", risk_check_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("response_generation", response_generation_node)

    workflow.set_entry_point("classifier")

    # Classifier → planner or response directly
    workflow.add_conditional_edges(
        "classifier",
        route_after_classifier,
        {
            "planner": "planner",
            "response_generation": "response_generation",
        },
    )

    # Planner → tool decision or response directly
    workflow.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "tool_decision": "tool_decision",
            "response_generation": "response_generation",
        },
    )

    # Tool decision → execution or response directly
    workflow.add_conditional_edges(
        "tool_decision",
        route_after_tool_decision,
        {
            "tool_execution": "tool_execution",
            "response_generation": "response_generation",
        },
    )

    # Tool execution → validation / retry / response
    workflow.add_conditional_edges(
        "tool_execution",
        route_after_tool_execution,
        {
            "validation": "validation",
            "retry": "retry",
            "response_generation": "response_generation",
        },
    )

    # Validation → retry / risk check / response
    workflow.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "retry": "retry",
            "risk_check": "risk_check",
            "response_generation": "response_generation",
        },
    )

    # Retry → tool execution / risk check / response
    workflow.add_conditional_edges(
        "retry",
        route_after_retry,
        {
            "tool_execution": "tool_execution",
            "risk_check": "risk_check",
            "response_generation": "response_generation",
        },
    )

    # Risk check → human review / response
    workflow.add_conditional_edges(
        "risk_check",
        route_after_risk_check,
        {
            "human_review": "human_review",
            "response_generation": "response_generation",
        },
    )

    # Human review → tool execution / response
    workflow.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {
            "tool_execution": "tool_execution",
            "response_generation": "response_generation",
        },
    )

    workflow.add_edge("response_generation", END)

    return workflow.compile()


def get_finance_app():
    """Backward-compatible alias for the compiled workflow app."""
    return create_finance_graph()


class FinanceWorkflowConfig:
    """Simple config container for workflow helpers."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries


workflow_config = {"name": "finance_workflow", "max_retries": 3}


def reset_workflow_state():
    """Reset any cached workflow state if needed."""
    return None


# Test function
def run_agent(user_input: str):
    initial_state = {
        "messages": [{"role": "user", "content": user_input}],
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
        "user_id": "user_123",
        "transaction_amount": None,
        "recipient_account": None
    }
    
    result = create_finance_graph().invoke(initial_state)
    return result