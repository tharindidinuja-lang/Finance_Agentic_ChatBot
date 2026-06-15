# nodes/risk_check_node.py
from state.finance_state import FinanceState
from config.constants import (
    DAILY_TRANSFER_LIMIT, 
    RISK_THRESHOLD_HIGH, 
    RISK_THRESHOLD_MEDIUM
)
from typing import Dict, Any, List

def risk_check_node(state: FinanceState) -> FinanceState:
    """
    Evaluate transaction risk based on multiple factors.
    Returns risk score (0-100) and flags for human review.
    """
    
    risk_score = 0
    risk_factors = []
    
    # Factor 1: Transaction amount
    amount = state.get("transaction_amount") or 0
    if amount > DAILY_TRANSFER_LIMIT:
        risk_score += 40
        risk_factors.append(f"Amount exceeds daily limit: ${amount}")
    elif amount > DAILY_TRANSFER_LIMIT * 0.7:
        risk_score += 20
        risk_factors.append(f"High amount: ${amount}")
    
    # Factor 2: New recipient (simulated)
    recipient = state.get("recipient_account", "")
    if is_new_recipient(recipient, state["user_id"]):
        risk_score += 25
        risk_factors.append("Transaction to new recipient")
    
    # Factor 3: Suspicious transaction patterns
    if is_suspicious_pattern(state):
        risk_score += 30
        risk_factors.append("Suspicious pattern detected")
    
    # Factor 4: Recent failed attempts
    retry_count = state.get("retry_count", 0)
    if retry_count > 0:
        risk_score += 10 * retry_count
        risk_factors.append(f"Previous failures: {retry_count}")
    
    # Factor 5: Time of day (simulated)
    if is_off_hours():
        risk_score += 15
        risk_factors.append("Off-hours transaction")
    
    # Cap at 100
    risk_score = min(risk_score, 100)
    
    # Determine if human review is needed
    needs_review = risk_score >= RISK_THRESHOLD_HIGH
    
    state["risk_score"] = risk_score
    state["risk_factors"] = risk_factors
    state["needs_human_review"] = needs_review
    
    if needs_review:
        state["fraud_flag"] = True
    
    return state

def is_new_recipient(account_number: str, user_id: str) -> bool:
    """Check if this recipient has been used before"""
    # Simulated - would check transaction history
    known_recipients = ["123456789"]  # Previously used accounts
    return account_number not in known_recipients

def is_suspicious_pattern(state: FinanceState) -> bool:
    """Check for suspicious patterns like rapid successive transfers"""
    # Simulated - would check velocity
    return False

def is_off_hours() -> bool:
    """Check if transaction is outside business hours (9am-5pm)"""
    from datetime import datetime
    current_hour = datetime.now().hour
    return current_hour < 9 or current_hour > 17

# Conditional edge function
def after_risk_check(state: FinanceState) -> str:
    """Route based on risk score"""
    
    if state.get("needs_human_review", False):
        return "human_review"
    else:
        return "response_generation"

if __name__ == "__main__":
    test_state = {
        "transaction_amount": 15000,  # $15k (over limit)
        "recipient_account": "987654321",  # New recipient
        "user_id": "user_123",
        "retry_count": 0
    }
    
    result = risk_check_node(test_state)
    print(f"Risk score: {result['risk_score']}")
    print(f"Risk factors: {result['risk_factors']}")
    print(f"Needs human review: {result['needs_human_review']}")