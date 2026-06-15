# nodes/planner_node.py
from state.finance_state import FinanceState
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config.constants import MODEL_NAME, TEMPERATURE
from utils.message_utils import get_message_content
import json
from typing import List, Dict

def planner_node(state: FinanceState) -> FinanceState:
    """
    Break user request into a step-by-step plan.
    Uses LLM to generate structured plan or rule-based for simple cases.
    """
    
    # Read intent from state (set by classifier); fall back to first plan step
    intent = state.get("intent") or (state["current_plan"][0] if state["current_plan"] else "general_query")
    
    # Simple rule-based plans (faster, deterministic)
    if intent in ("balance_check", "check_balance", "get_account_balance"):
        plan = ["get_account_balance"]
        
    elif intent in ("transfer_money", "validate_recipient_account"):
        plan = [
            "validate_recipient_account",
            "check_sufficient_balance", 
            "execute_fund_transfer",
            "log_transaction"
        ]
        
    elif intent in ("stock_price", "get_stock_price"):
        plan = ["get_stock_price"]

    elif intent == "web_search":
        plan = ["web_search"]

    elif intent in ("general_query", ""):
        plan = []

    elif intent in ("transaction_history", "get_transaction_history"):
        plan = ["get_transaction_history"]
        
    elif intent == "fraud_report":
        plan = [
            "get_transaction_history",
            "run_fraud_detection",
            "generate_fraud_report"
        ]
        
    else:
        # Use LLM for complex queries
        plan = llm_based_planning(state, intent)
    
    state["current_plan"] = plan
    state["current_step"] = 0
    
    return state

def llm_based_planning(state: FinanceState, intent: str) -> List[str]:
    """Use LLM to generate a plan for complex queries"""
    
    llm = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)
    
    system_prompt = """You are a financial planning agent. Break down the user's request into a sequence of tool calls.
    
Available tools:
- get_account_balance: Check account balance
- get_transaction_history: Get recent transactions
- fetch_stock_price: Get current stock price
- validate_recipient_account: Check if recipient account exists
- check_sufficient_balance: Verify funds availability
- execute_fund_transfer: Transfer money between accounts
- run_fraud_detection: Analyze transactions for fraud
- calculate_loan_emi: Calculate loan installments

Return ONLY a JSON list of tool names in execution order.
Example: ["get_transaction_history", "run_fraud_detection"]"""
    
    user_message = get_message_content(state["messages"][-1]) if state.get("messages") else ""
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User request: {user_message}\nIntent: {intent}\nPlan:")
        ])
    except Exception:
        # If the LLM is unavailable, avoid inventing a transaction-history tool call.
        return []
    
    try:
        # Extract JSON list from response
        plan = json.loads(response.content)
        if isinstance(plan, list):
            return plan
    except:
        pass
    
    # Fallback
    return ["get_account_balance"]

# Test function (run this file directly)
if __name__ == "__main__":
    test_state = {
        "messages": [{"role": "user", "content": "Transfer $500 to my savings"}],
        "current_plan": ["transfer_money"],
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
    
    result = planner_node(test_state)
    print(f"Generated plan: {result['current_plan']}")