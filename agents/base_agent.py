# agents/base_agent.py
"""Abstract base agent class with common methods for all agents"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from state.finance_state import FinanceState
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Defines the interface that all specific agents must implement.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            name: Agent name/identifier
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.conversation_history: List[Dict[str, str]] = []
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "total_messages": 0,
            "total_errors": 0
        }
        
        logger.info(f"Initialized agent: {name}")
    
    @abstractmethod
    def process(self, user_input: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Process user input and return response.
        
        Args:
            user_input: The user's message
            user_id: Unique identifier for the user
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing response and metadata
        """
        pass
    
    @abstractmethod
    def get_state(self, user_id: str) -> Optional[FinanceState]:
        """
        Retrieve the current state for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Current FinanceState or None if not found
        """
        pass
    
    @abstractmethod
    def reset_state(self, user_id: str) -> FinanceState:
        """
        Reset conversation state for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Fresh FinanceState
        """
        pass
    
    def log_interaction(self, user_input: str, response: str, error: Optional[str] = None):
        """
        Log agent interaction for audit and debugging.
        
        Args:
            user_input: User's message
            response: Agent's response
            error: Optional error message
        """
        self.metadata["total_messages"] += 1
        if error:
            self.metadata["total_errors"] += 1
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "response": response,
            "error": error,
            "agent": self.name
        }
        
        # Log to file
        import json
        with open("data/agent_logs.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        if error:
            logger.error(f"Error in agent {self.name}: {error}")
        else:
            logger.info(f"Agent {self.name} processed message")
    
    def validate_input(self, user_input: str) -> bool:
        """
        Validate user input before processing.
        
        Args:
            user_input: User's message
            
        Returns:
            True if valid, False otherwise
        """
        if not user_input or not isinstance(user_input, str):
            return False
        if len(user_input.strip()) == 0:
            return False
        if len(user_input) > 10000:  # Max length limit
            return False
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get agent performance metrics.
        
        Returns:
            Dictionary with metrics
        """
        error_rate = (self.metadata["total_errors"] / self.metadata["total_messages"]) if self.metadata["total_messages"] > 0 else 0
        
        return {
            "agent_name": self.name,
            "total_messages": self.metadata["total_messages"],
            "total_errors": self.metadata["total_errors"],
            "error_rate": error_rate,
            "created_at": self.metadata["created_at"]
        }
    
    def __repr__(self) -> str:
        return f"<BaseAgent(name={self.name}, messages={self.metadata['total_messages']})>"


# Simple test
if __name__ == "__main__":
    # This will raise TypeError because BaseAgent is abstract
    # But we can test the validation methods
    class TestAgent(BaseAgent):
        def process(self, user_input, user_id, **kwargs):
            return {"response": "test"}
        
        def get_state(self, user_id):
            return None
        
        def reset_state(self, user_id):
            from state.finance_state import FinanceState
            return FinanceState(messages=[])
    
    agent = TestAgent("test_agent")
    print(f"Valid input: {agent.validate_input('Hello')}")
    print(f"Invalid input (empty): {agent.validate_input('')}")
    print(f"Agent: {agent}")