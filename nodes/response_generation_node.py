# nodes/response_generation_node.py
from state.finance_state import FinanceState
# pyrefly: ignore [missing-import]
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config.constants import MODEL_NAME, TEMPERATURE
from utils.message_utils import get_message_content

def response_generation_node(state: FinanceState) -> FinanceState:
    """
    Generate final user-friendly response based on tool results and state.
    """
    
    # Check for error conditions first
    if state.get("validation_status") == "failed_permanent":
        response = generate_error_response(state)
        
    elif state.get("human_review_decision") == "denied":
        response = generate_denial_response(state)
        
    elif state.get("human_review_decision") == "modified":
        response = generate_modification_response(state)
        
    elif state.get("fraud_flag") and not state.get("human_approved"):
        response = generate_fraud_alert_response(state)
        
    else:
        # Normal response based on tool results
        response = generate_normal_response(state)
    
    # Add response to messages
    state["messages"].append({"role": "assistant", "content": response})
    
    return state

def generate_general_knowledge_response(state: FinanceState) -> str:
    """Provide simple finance explanations for general questions without relying on the LLM."""
    last_message = get_message_content(state.get("messages", [])[-1]) if state.get("messages") else ""
    text = last_message.lower()

    if "etf" in text:
        return (
            "An ETF (exchange-traded fund) is a basket of investments, such as stocks or bonds, "
            "that trades on an exchange like a stock. It lets you buy a diversified portfolio in one transaction."
        )

    if "epf" in text:
        return (
            "EPF usually means Employees' Provident Fund, which is a retirement savings scheme where "
            "employees and employers contribute regularly to build a retirement fund."
        )

    if "apr" in text:
        return (
            "APR stands for Annual Percentage Rate. It is the yearly cost of borrowing money, "
            "including interest and some fees, expressed as a percentage."
        )

    return ""


def generate_normal_response(state: FinanceState) -> str:
    """Generate response from successful tool execution"""
    
    if not state.get("tool_results"):
        fallback = generate_general_knowledge_response(state)
        if fallback:
            return fallback
        # Safe static message — never call OpenAI for a general query
        last_msg = get_message_content(state.get("messages", [])[-1]) if state.get("messages") else ""
        if last_msg:
            return f"I'm your financial assistant. I can help with account balances, fund transfers, stock prices, and more. Could you clarify what you'd like help with?"
        return "Hello! I'm your financial assistant. How can I help you today?"
    
    last_result = state["tool_results"][-1]
    tool_name = last_result["tool_name"]
    result_data = last_result.get("result", {})
    
    # Tool-specific response formatting
    if tool_name == "get_account_balance":
        balance = result_data.get("balance", 0)
        account_type = result_data.get("account_type", "account")
        return f"Your {account_type} account balance is **${balance:,.2f}**."
    
    elif tool_name == "execute_fund_transfer":
        amount = state.get("transaction_amount", 0)
        recipient = state.get("recipient_account", "recipient")
        return f"Transfer of **${amount:,.2f}** to account {recipient} has been completed successfully. A confirmation number has been sent to your registered email."
    
    elif tool_name == "fetch_stock_price":
        symbol = result_data.get("symbol", "the stock")
        price = result_data.get("price", 0)
        change = result_data.get("change", 0)
        direction = "up" if change >= 0 else "down"
        return f"{symbol} is currently **${price:.2f}** ({direction} ${abs(change):.2f} today)."
        
    elif tool_name == "get_stock_price":
        symbol = result_data.get("symbol", "the stock")
        price_info = result_data.get("price_info", "")
        if price_info:
            return f"Here is the latest price information for **{symbol}**:\n\n{price_info}"
        return f"I retrieved data for **{symbol}**, but no price details were returned. Please check a financial site like Yahoo Finance for the latest quote."
    
    elif tool_name == "web_search":
        answer = result_data.get("answer", "")
        results = result_data.get("results", [])
        if answer:
            response = answer
            if results:
                sources = ", ".join(r["url"] for r in results[:2] if r.get("url"))
                if sources:
                    response += f"\n\n*Sources: {sources}*"
            return response
        if results:
            return "\n".join(f"- {r.get('content', '')[:200]}" for r in results[:3] if r.get("content"))
        return "I searched the web but could not find a clear answer. Please try rephrasing your question."
    
    elif tool_name == "get_transaction_history":
        transactions = result_data.get("transactions", [])
        if not transactions:
            return "No recent transactions found."
        
        response = "**Your recent transactions:**\n"
        for tx in transactions[:5]:  # Show last 5
            response += f"- {tx.get('date', 'N/A')}: ${tx.get('amount', 0):,.2f} - {tx.get('description', 'Unknown')}\n"
        return response
    
    else:
        # Try LLM for truly unexpected tool types, but guard against auth failures
        try:
            return llm_generate_response(state)
        except Exception:
            return "I processed your request but encountered an issue generating a response. Please try again."

def generate_error_response(state: FinanceState) -> str:
    """Generate response for permanent failures"""
    retry_count = state.get("retry_count", 0)
    error_msg = state.get("retry_message", "Operation failed after multiple attempts")
    
    return f"❌ I'm unable to complete your request. {error_msg} Please contact customer support if the issue persists."

def generate_denial_response(state: FinanceState) -> str:
    """Generate response for human-denied transactions"""
    risk_factors = state.get("risk_factors", [])
    risk_factors_text = ", ".join(risk_factors) if risk_factors else "security concerns"
    
    return f"❌ Your transaction has been declined due to {risk_factors_text}. Please contact customer service at 1-800-BANK-SAFE for assistance."

def generate_modification_response(state: FinanceState) -> str:
    """Generate response for modified transactions"""
    new_amount = state.get("transaction_amount", 0)
    
    return f"✅ Your transaction has been approved with a modified amount of **${new_amount:,.2f}**. The original amount was adjusted due to risk guidelines."

def generate_fraud_alert_response(state: FinanceState) -> str:
    """Generate response when fraud is suspected"""
    return f"⚠️ **Fraud Alert**: This transaction has been flagged for unusual activity. Our fraud detection team has been notified. Please verify your identity by calling 1-800-BANK-SAFE."

def llm_generate_response(state: FinanceState) -> str:
    """Use LLM to generate a response for complex cases"""
    
    llm = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)
    
    # Prepare context
    normalized_messages = [msg for msg in state.get('messages', []) if get_message_content(msg)]
    last_user_message = get_message_content(normalized_messages[-1]) if normalized_messages else 'N/A'

    context = f"""
    User request: {last_user_message}
    Tool results: {state.get('tool_results', [])}
    Risk score: {state.get('risk_score', 0)}
    Validation status: {state.get('validation_status', 'unknown')}
    """
    
    response = llm.invoke([
        SystemMessage(content="You are a helpful financial assistant. Provide clear, professional responses. Use currency formatting ($X,XXX.XX). Be concise."),
        HumanMessage(content=f"Based on this context, generate a response for the user:\n\n{context}")
    ])
    
    return response.content

if __name__ == "__main__":
    # Test with balance response
    test_state = {
        "tool_results": [{
            "tool_name": "get_account_balance",
            "result": {"balance": 5420.50, "account_type": "checking"}
        }],
        "messages": [{"role": "user", "content": "What's my balance?"}],
        "validation_status": "passed",
        "retry_count": 0
    }
    
    result = response_generation_node(test_state)
    print(f"Response: {get_message_content(result['messages'][-1])}")