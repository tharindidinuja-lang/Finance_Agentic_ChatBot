# nodes/classifier_node.py
"""Classifier node for intent detection"""

import re
from state.finance_state import FinanceState
from utils.amount_parser import AmountParser
from utils.message_utils import get_message_content


def is_web_search_needed(query: str) -> bool:
    """Determine if query requires real-time web search"""
    real_time_keywords = [
        "stock price", "current price", "today", "latest",
        "news", "weather", "what is", "who is", "when did",
        "explain", "tell me about", "define", "meaning of"
    ]
    return any(keyword in query.lower() for keyword in real_time_keywords)


def classifier_node(state: FinanceState) -> FinanceState:
    """Classify user intent and clear stale transaction state from previous turns."""

    # Reset transient transaction state for a fresh request
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

    messages = state.get("messages", [])
    if not messages:
        state["intent"] = "general_query"
        return state
    
    last_message = get_message_content(messages[-1]) if messages else ""
    last_message_lower = last_message.lower()
    
    # DEBUG: Print the query without emojis to prevent encoding crashes
    print(f"\n[DEBUG] User query: {last_message}")

    # Initialize extracted_entities for test compatibility
    state["extracted_entities"] = {}

    # ========================================================================
    # Balance check (Check this first to avoid false positives with "what is my balance")
    # ========================================================================
    
    balance_keywords = ("balance", "how much money", "how much do i have", "current balance")
    if any(keyword in last_message_lower for keyword in balance_keywords):
        state["intent"] = "balance_check"
        state["current_plan"] = ["get_account_balance"]
        print(f"[Classifier] -> balance_check")
        print(f"[DEBUG] Detected intent: {state['intent']}")
        return state

    # ========================================================================
    # Transfer money
    # ========================================================================
    
    transfer_keywords = ("transfer", "send", "move funds", "pay to", "pay ", "wire", "deposit")
    if any(keyword in last_message_lower for keyword in transfer_keywords):
        state["intent"] = "transfer_money"
        state["current_plan"] = ["validate_recipient", "check_balance", "execute_transfer"]
        
        # Extract amount
        amount_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', last_message)
        if amount_match:
            val = float(amount_match.group(1).replace(',', ''))
            state["transaction_amount"] = val
            state["extracted_entities"]["amount"] = val
            
        # Extract recipient account
        account_match = re.search(r'account #?(\d+)', last_message_lower)
        if account_match:
            state["recipient_account"] = account_match.group(1)
            state["extracted_entities"]["recipient"] = account_match.group(1)
        
        print(f"[Classifier] -> transfer_money")
        print(f"[DEBUG] Detected intent: {state['intent']}")
        return state

    # ========================================================================
    # Transaction history
    # ========================================================================
    
    history_keywords = ("transaction history", "transactions", "history", "last 5", "recent")
    if any(keyword in last_message_lower for keyword in history_keywords):
        state["intent"] = "transaction_history"
        state["current_plan"] = ["get_transaction_history"]
        print(f"[Classifier] -> transaction_history")
        print(f"[DEBUG] Detected intent: {state['intent']}")
        return state

    # ========================================================================
    # Fraud report
    # ========================================================================
    
    fraud_keywords = ("fraud", "suspicious", "hacked", "unauthorized", "charge", "scam", "compromised")
    if any(keyword in last_message_lower for keyword in fraud_keywords):
        state["intent"] = "fraud_report"
        state["current_plan"] = ["fraud_report"]
        print(f"[Classifier] -> fraud_report")
        print(f"[DEBUG] Detected intent: {state['intent']}")
        return state

    # ========================================================================
    # Stock price or Web search / general knowledge questions
    # ========================================================================
    
    # Patterns for general knowledge questions
    general_question_patterns = [
        r'what is (a|an|the)?\s+\w+',      # "what is X"
        r'what\'s (a|an|the)?\s+\w+',      # "what's X"
        r'can you explain',                 # "can you explain"
        r'tell me about',                   # "tell me about"
        r'what does \w+ mean',              # "what does X mean"
        r'define \w+',                      # "define X"
    ]
    
    is_general_question = any(re.search(pattern, last_message_lower) for pattern in general_question_patterns)
    is_stock_query = any(word in last_message_lower for word in ["stock", "price", "share", "ticker"])
    
    # If it's a stock query, classify as stock_price and plan for get_stock_price
    if is_stock_query:
        state["intent"] = "stock_price"
        state["current_plan"] = ["get_stock_price"]
        print(f"[Classifier] -> stock_price intent (query: {last_message[:50]})")
        print(f"[DEBUG] Detected intent: {state['intent']}")
        return state
        
    # If it's a general question or web search query, use web search
    if is_general_question or is_web_search_needed(last_message):
        state["intent"] = "web_search"
        state["current_plan"] = ["web_search"]
        print(f"[Classifier] -> web_search intent (query: {last_message[:50]})")
        print(f"[DEBUG] Detected intent: {state['intent']}")
        return state

    # ========================================================================
    # Default - general query
    # ========================================================================
    
    state["intent"] = "general_query"
    state["current_plan"] = []
    print(f"[Classifier] -> general_query (default)")
    print(f"[DEBUG] Detected intent: {state['intent']}")
    
    return state