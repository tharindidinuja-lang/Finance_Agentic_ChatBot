# tests/test_workflow.py
"""End-to-end workflow tests for finance agent"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch
from workflows.finance_graph import create_finance_graph
from state.finance_state import create_initial_state
from utils.message_utils import get_message_role, get_message_content


# ---------------------------------------------------------------------------
# Shared setUp/tearDown helpers via mixin
# ---------------------------------------------------------------------------

class TestWorkflow(unittest.TestCase):
    """End-to-end workflow tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_finance_graph()
        self.user_id = "test_user_001"
        
        # Mock is_off_hours to always return False to prevent time-of-day-dependent failures
        import nodes.risk_check_node
        self.original_is_off_hours = nodes.risk_check_node.is_off_hours
        nodes.risk_check_node.is_off_hours = lambda: False
        
        # Mock ChatOpenAI.invoke
        # pyrefly: ignore [missing-import]
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import AIMessage
        self.original_invoke = ChatOpenAI.invoke
        
        def mock_invoke(self_llm, messages, **kwargs):
            system_msg = messages[0].content if messages else ""
            user_msg = messages[1].content if len(messages) > 1 else ""
            
            if "financial planning agent" in system_msg:
                if "weather" in user_msg.lower():
                    return AIMessage(content='["web_search"]')
                return AIMessage(content='[]')
            else:
                if "weather" in user_msg.lower() or "weather" in system_msg.lower():
                    return AIMessage(content="I'm sorry, but I can't assist with weather queries. I am a financial assistant.")
                return AIMessage(content="I am a helpful financial assistant response.")
                
        ChatOpenAI.invoke = mock_invoke
        
    def tearDown(self):
        import nodes.risk_check_node
        nodes.risk_check_node.is_off_hours = self.original_is_off_hours
        
        # pyrefly: ignore [missing-import]
        from langchain_openai import ChatOpenAI
        ChatOpenAI.invoke = self.original_invoke
    
    def create_and_run(self, user_message: str):
        """Helper to create state and run workflow"""
        state = create_initial_state(self.user_id)
        state["messages"].append({"role": "user", "content": user_message})
        return self.app.invoke(state)
    
    def test_balance_check_workflow(self):
        """Test complete balance check workflow"""
        result = self.create_and_run("What's my checking account balance?")
        
        # Check that we got a response
        self.assertGreater(len(result["messages"]), 1)
        
        # Check that assistant responded
        assistant_messages = [m for m in result["messages"] if m.get("role") == "assistant"]
        self.assertGreater(len(assistant_messages), 0)
        
        # Check response contains balance info
        response = assistant_messages[0]["content"]
        self.assertIn("balance", response.lower())
    
    def test_transfer_workflow_low_risk(self):
        """Test low risk transfer workflow"""
        result = self.create_and_run("Transfer $100 to my savings account")
        
        # Check workflow completed
        self.assertIn("validation_status", result)
        
        # Check transaction was processed
        tool_results = result.get("tool_results", [])
        transfer_results = [t for t in tool_results if t.get("tool_name") == "execute_fund_transfer"]
        
        if transfer_results:
            self.assertTrue(transfer_results[-1].get("status") == "success")
    
    @patch('builtins.input', return_value='yes')
    def test_transfer_workflow_high_risk(self, mock_input):
        """Test high risk transfer workflow (should trigger review)"""
        result = self.create_and_run("Transfer $15000 to crypto_exchange_123")
        
        # Check that risk was detected
        self.assertGreaterEqual(result.get("risk_score", 0), 50)
        
        # Check that human review was triggered
        # Note: In automated test, human review might not be completed
        # This just verifies the state
        self.assertIn("needs_human_review", result)
    
    def test_stock_price_workflow(self):
        """Test stock price lookup workflow"""
        result = self.create_and_run("What's Apple stock price?")
        
        # Check we got a response
        assistant_messages = [m for m in result["messages"] if m.get("role") == "assistant"]
        self.assertGreater(len(assistant_messages), 0)
    
    def test_conversation_context(self):
        """Test that conversation context is maintained"""
        # First message
        result1 = self.create_and_run("My name is John")
        
        # Second message in same conversation
        state = create_initial_state(self.user_id)
        state["messages"] = result1["messages"]  # Continue conversation
        state["messages"].append({"role": "user", "content": "What's my name?"})
        result2 = self.app.invoke(state)
        
        # Check that context was maintained
        assistant_messages = [m for m in result2["messages"] if m.get("role") == "assistant"]
        if assistant_messages:
            response = assistant_messages[-1]["content"]
            # Should have remembered the name
            self.assertTrue("John" in response or "john" in response.lower())
    
    def test_error_handling(self):
        """Test error handling in workflow"""
        # Send empty message
        result = self.create_and_run("")
        
        # Should still return a response
        assistant_messages = [m for m in result["messages"] if m.get("role") == "assistant"]
        self.assertGreater(len(assistant_messages), 0)
    
    def test_validation_failure(self):
        """Test validation failure handling"""
        # Try invalid transaction
        result = self.create_and_run("Transfer $-100 to account")
        
        # Should have validation status
        self.assertIn("validation_status", result)
    
    def test_workflow_completion(self):
        """Test that workflow completes properly"""
        result = self.create_and_run("What's my balance?")
        
        # Check that all plan steps were processed
        current_step = result.get("current_step", 0)
        current_plan = result.get("current_plan", [])
        
        # If there was a plan, it should be completed
        if current_plan:
            self.assertGreaterEqual(current_step, len(current_plan))
    
    def test_multi_step_transaction(self):
        """Test multi-step transaction (validate, check, execute)"""
        result = self.create_and_run("Send $500 to account #123456789")
        
        # Check that multiple tools were executed
        tool_results = result.get("tool_results", [])
        tool_names = [t.get("tool_name") for t in tool_results]
        
        # Should have validation and execution steps
        self.assertTrue(
            any("validate" in name for name in tool_names) or
            any("check" in name for name in tool_names)
        )


class TestWorkflowEdgeCases(unittest.TestCase):
    """Test edge cases for workflow"""
    
    def setUp(self):
        self.app = create_finance_graph()
        self.user_id = "edge_case_user"
        
        # Mock is_off_hours to always return False to prevent time-of-day-dependent failures
        import nodes.risk_check_node
        self.original_is_off_hours = nodes.risk_check_node.is_off_hours
        nodes.risk_check_node.is_off_hours = lambda: False
        
        # Mock ChatOpenAI.invoke
        # pyrefly: ignore [missing-import]
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import AIMessage
        self.original_invoke = ChatOpenAI.invoke
        
        def mock_invoke(self_llm, messages, **kwargs):
            system_msg = messages[0].content if messages else ""
            user_msg = messages[1].content if len(messages) > 1 else ""
            
            if "financial planning agent" in system_msg:
                if "weather" in user_msg.lower():
                    return AIMessage(content='["web_search"]')
                return AIMessage(content='[]')
            else:
                if "weather" in user_msg.lower() or "weather" in system_msg.lower():
                    return AIMessage(content="I'm sorry, but I can't assist with weather queries. I am a financial assistant.")
                return AIMessage(content="I am a helpful financial assistant response.")
                
        ChatOpenAI.invoke = mock_invoke
        
    def tearDown(self):
        import nodes.risk_check_node
        nodes.risk_check_node.is_off_hours = self.original_is_off_hours
        
        # pyrefly: ignore [missing-import]
        from langchain_openai import ChatOpenAI
        ChatOpenAI.invoke = self.original_invoke
    
    def create_and_run(self, user_message: str):
        state = create_initial_state(self.user_id)
        state["messages"].append({"role": "user", "content": user_message})
        return self.app.invoke(state)
    
    def test_very_long_message(self):
        """Test very long user message"""
        long_message = "A" * 5000
        result = self.create_and_run(long_message)
        
        # Should still process
        self.assertIsNotNone(result)
    
    def test_special_characters(self):
        """Test messages with special characters"""
        special_message = "Transfer $1,000!!! @#$% to account #123"
        result = self.create_and_run(special_message)
        
        # Should handle special characters
        self.assertIsNotNone(result)
    
    def test_non_financial_query(self):
        """Test non-financial query"""
        result = self.create_and_run("What's the weather like today?")
        
        # Should respond gracefully
        assistant_messages = [m for m in result["messages"] if m.get("role") == "assistant"]
        if assistant_messages:
            response = assistant_messages[0]["content"]
            # Should indicate it's not a financial query
            self.assertTrue(
                "can't" in response.lower() or 
                "financial" in response.lower() or
                "sorry" in response.lower()
            )


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)