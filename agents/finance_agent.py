# agents/finance_agent.py
"""Finance Agent - Concrete implementation for banking/finance chatbot"""

from agents.base_agent import BaseAgent
from state.finance_state import FinanceState
from workflows.finance_graph import create_finance_graph
from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging
import os
from memory.conversation_buffer import ConversationBuffer
from memory.transaction_memory import TransactionMemory
from memory.risk_memory import RiskMemory
from utils.message_utils import get_message_content, get_message_role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinanceAgent(BaseAgent):
    """
    Finance Agent for banking transactions, balance checks, transfers, etc.
    Uses LangGraph workflow for multi-step reasoning.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Finance Agent.
        
        Args:
            config: Configuration dictionary with settings
        """
        super().__init__(name="FinanceAgent", config=config)
        
        # Create the LangGraph workflow
        self.graph = create_finance_graph()
        
        # Store states per user (in production, use Redis/database)
        self.user_states: Dict[str, FinanceState] = {}
        
        # Load persistence if configured
        self.persistence_dir = config.get("persistence_dir", "data/user_states") if config else "data/user_states"
        os.makedirs(self.persistence_dir, exist_ok=True)
        
        logger.info(f"FinanceAgent initialized with persistence dir: {self.persistence_dir}")
    
    def process(self, user_input: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Process user input through the LangGraph workflow.
        
        Args:
            user_input: User's message
            user_id: User identifier
            **kwargs: Additional parameters (e.g., reset_conversation)
            
        Returns:
            Dictionary with response and metadata
        """
        # Validate input
        if not self.validate_input(user_input):
            return {
                "response": "I couldn't understand that. Please provide a valid message.",
                "error": "Invalid input",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Check if we should reset conversation
        if kwargs.get("reset_conversation", False):
            self.reset_state(user_id)
        
        # Get or create state for this user
        state = self.get_state(user_id)
        if state is None:
            state = self.reset_state(user_id)
        
        # Add user message to state
        state["messages"].append({"role": "user", "content": user_input})
        
        try:
            # Run the LangGraph workflow
            result_state = self.graph.invoke(state)
            
            # Extract the assistant's response
            assistant_messages = [msg for msg in result_state["messages"] if get_message_role(msg) == "assistant"]
            response = get_message_content(assistant_messages[-1]) if assistant_messages else "I've processed your request."
            
            # Save the updated state
            self.user_states[user_id] = result_state
            self.persist_state(user_id, result_state)
            
            # Log successful interaction
            self.log_interaction(user_input, response)
            
            # Prepare response metadata
            return {
                "response": response,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "risk_score": result_state.get("risk_score", 0),
                "transaction_completed": bool(result_state.get("tool_results")),
                "needs_human_review": result_state.get("needs_human_review", False),
                "validation_status": result_state.get("validation_status", "unknown")
            }
            
        except Exception as e:
            error_msg = str(e)
            self.log_interaction(user_input, "", error=error_msg)
            
            return {
                "response": f"I encountered an error while processing your request. Please try again later.",
                "error": error_msg,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_state(self, user_id: str) -> Optional[FinanceState]:
        """
        Retrieve state for a user from memory or disk.
        
        Args:
            user_id: User identifier
            
        Returns:
            FinanceState or None
        """
        # Check memory first
        if user_id in self.user_states:
            return self.user_states[user_id]
        
        # Try to load from disk
        state_file = os.path.join(self.persistence_dir, f"{user_id}.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    state_data = json.load(f)
                return self._deserialize_state(state_data)
            except Exception as e:
                logger.error(f"Failed to load state for {user_id}: {e}")
        
        return None
    
    def reset_state(self, user_id: str) -> FinanceState:
        """
        Reset conversation state for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Fresh FinanceState
        """
        fresh_state: FinanceState = {
            "messages": [],
            "current_plan": [],
            "current_step": 0,
            "tool_calls": [],
            "tool_results": [],
            "validation_status": "pending",
            "validation_message": "",
            "retry_count": 0,
            "retry_action": "none",
            "retry_message": "",
            "risk_score": 0,
            "risk_factors": [],
            "fraud_flag": False,
            "needs_human_review": False,
            "human_approved": None,
            "human_review_decision": None,
            "human_review_notes": None,
            "user_id": user_id,
            "transaction_amount": None,
            "recipient_account": None
        }
        
        self.user_states[user_id] = fresh_state
        self.persist_state(user_id, fresh_state)
        
        logger.info(f"Reset state for user: {user_id}")
        return fresh_state
    
    def persist_state(self, user_id: str, state: FinanceState):
        """
        Save state to disk for persistence.
        
        Args:
            user_id: User identifier
            state: Current FinanceState
        """
        state_file = os.path.join(self.persistence_dir, f"{user_id}.json")
        
        # Convert state to serializable format
        serializable_state = self._serialize_state(state)
        
        try:
            with open(state_file, 'w') as f:
                json.dump(serializable_state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to persist state for {user_id}: {e}")
    
    def _serialize_state(self, state: FinanceState) -> Dict[str, Any]:
        """
        Convert FinanceState to JSON-serializable format.
        
        Args:
            state: FinanceState object
            
        Returns:
            Serializable dictionary
        """
        serialized = {}
        for key, value in state.items():
            if key == "messages":
                # Messages are already serializable
                serialized[key] = value
            elif key in ["tool_calls", "tool_results", "risk_factors"]:
                serialized[key] = value
            elif isinstance(value, (int, float, str, bool, type(None))):
                serialized[key] = value
            elif isinstance(value, list):
                serialized[key] = value
            else:
                serialized[key] = str(value)
        return serialized
    
    def _deserialize_state(self, data: Dict[str, Any]) -> FinanceState:
        """
        Convert serialized data back to FinanceState.
        
        Args:
            data: Serialized state dictionary
            
        Returns:
            FinanceState object
        """
        return FinanceState(**data)
    
    def get_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of the conversation for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Summary dictionary
        """
        state = self.get_state(user_id)
        if not state:
            return {"error": "No conversation found for this user"}
        
        messages = state.get("messages", [])
        user_messages = [m for m in messages if get_message_role(m) == "user"]
        assistant_messages = [m for m in messages if get_message_role(m) == "assistant"]
        
        return {
            "user_id": user_id,
            "total_messages": len(messages),
            "user_turns": len(user_messages),
            "assistant_turns": len(assistant_messages),
            "last_interaction": messages[-1].get("timestamp", "Unknown") if messages else "None",
            "total_transactions": len(state.get("tool_results", [])),
            "latest_risk_score": state.get("risk_score", 0)
        }
    
    def execute_batch(self, user_queries: list, user_id: str) -> list:
        """
        Execute multiple queries in sequence (batch mode).
        
        Args:
            user_queries: List of user messages
            user_id: User identifier
            
        Returns:
            List of responses
        """
        responses = []
        for query in user_queries:
            result = self.process(query, user_id)
            responses.append(result)
        return responses
    
    def get_agent_metrics(self) -> Dict[str, Any]:
        """
        Get detailed metrics for this agent.
        
        Returns:
            Dictionary with metrics
        """
        base_metrics = self.get_metrics()
        
        return {
            **base_metrics,
            "active_users": len(self.user_states),
            "persistence_enabled": True,
            "persistence_directory": self.persistence_dir
        }


# Convenience function to create a finance agent
def create_finance_agent(config: Optional[Dict[str, Any]] = None) -> FinanceAgent:
    """
    Factory function to create a FinanceAgent instance.
    
    Args:
        config: Optional configuration
        
    Returns:
        Configured FinanceAgent
    """
    default_config = {
        "persistence_dir": "data/user_states",
        "max_history": 100,
        "enable_logging": True
    }
    
    if config:
        default_config.update(config)
    
    return FinanceAgent(config=default_config)


# Demo and testing
if __name__ == "__main__":
    print("="*60)
    print("Finance Agent Demo")
    print("="*60)
    
    # Create agent
    agent = create_finance_agent()
    
    # Test queries
    test_queries = [
        "What's my checking account balance?",
        "Transfer $500 to account #987654321",
        "What's the current Apple stock price?",
        "Show me my recent transactions"
    ]
    
    user_id = "test_user_001"
    
    for query in test_queries:
        print(f"\n User: {query}")
        result = agent.process(query, user_id)
        print(f" Agent: {result['response']}")
        
        if result.get('risk_score', 0) > 0:
            print(f"Risk Score: {result['risk_score']}")
        
        if result.get('needs_human_review'):
            print("This transaction requires human review")
    
    # Show conversation summary
    print("\n" + "="*60)
    print("Conversation Summary")
    print("="*60)
    summary = agent.get_conversation_summary(user_id)
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Show agent metrics
    print("\n" + "="*60)
    print("Agent Metrics")
    print("="*60)
    metrics = agent.get_agent_metrics()
    for key, value in metrics.items():
        print(f"{key}: {value}")