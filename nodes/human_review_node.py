# nodes/human_review_node.py
from state.finance_state import FinanceState
from typing import Dict, Any

def human_review_node(state: FinanceState) -> FinanceState:
    """
    Route high-risk transactions to human reviewer.
    Uses LangGraph interrupt pattern.
    """
    
    if not state.get("needs_human_review", False):
        # Skip if not needed
        state["human_approved"] = True
        state["human_review_decision"] = "pending"
        return state
    
    # Prepare review data for human
    review_data = {
        "user_id": state["user_id"],
        "transaction_amount": state.get("transaction_amount", 0),
        "recipient_account": state.get("recipient_account", "Unknown"),
        "risk_score": state.get("risk_score", 0),
        "risk_factors": state.get("risk_factors", []),
        "tool_results": state.get("tool_results", []),
        "conversation": state["messages"]
    }
    
    # Display to human (in real implementation, this would be a UI or API call)
    print("\n" + "="*60)
    print("⚠️  HUMAN REVIEW REQUIRED ⚠️")
    print("="*60)
    print(f"User: {review_data['user_id']}")
    print(f"Amount: ${review_data['transaction_amount']:,.2f}")
    print(f"Recipient: {review_data['recipient_account']}")
    print(f"Risk Score: {review_data['risk_score']}/100")
    print(f"Risk Factors: {', '.join(review_data['risk_factors'])}")
    print("="*60)
    
    # Get human decision
    while True:
        decision = input("\nApprove this transaction? (yes/no/modify): ").lower()
        
        if decision == "yes":
            state["human_approved"] = True
            state["human_review_decision"] = "approved"
            state["human_review_notes"] = "Approved by human reviewer"
            break
            
        elif decision == "no":
            state["human_approved"] = False
            state["human_review_decision"] = "denied"
            state["human_review_notes"] = "Denied by human reviewer"
            break
            
        elif decision == "modify":
            new_amount = input("Enter modified amount: ")
            try:
                state["transaction_amount"] = float(new_amount)
                state["human_approved"] = True
                state["human_review_decision"] = "modified"
                state["human_review_notes"] = f"Amount modified to ${new_amount}"
                break
            except:
                print("Invalid amount. Please try again.")
        else:
            print("Please enter 'yes', 'no', or 'modify'")
    
    # Log the review
    log_human_review(state)
    
    return state

def log_human_review(state: FinanceState) -> None:
    """Log human review for audit compliance"""
    import json
    from datetime import datetime
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": state["user_id"],
        "decision": state.get("human_review_decision"),
        "notes": state.get("human_review_notes"),
        "risk_score": state.get("risk_score")
    }
    
    # Append to log file
    with open("data/human_review_log.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

# Conditional edge function
def after_human_review(state: FinanceState) -> str:
    """Route after human review"""
    
    if state.get("human_approved", False):
        return "tool_execution"  # Execute the approved transaction
    else:
        return "response_generation"  # Generate denial response

if __name__ == "__main__":
    test_state = {
        "needs_human_review": True,
        "user_id": "user_123",
        "transaction_amount": 15000,
        "recipient_account": "987654321",
        "risk_score": 75,
        "risk_factors": ["Amount exceeds daily limit", "New recipient"],
        "tool_results": [],
        "messages": [{"role": "user", "content": "Transfer $15000"}]
    }
    
    result = human_review_node(test_state)
    print(f"\nHuman approved: {result['human_approved']}")
    print(f"Decision: {result.get('human_review_decision')}")