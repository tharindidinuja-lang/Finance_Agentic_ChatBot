# tests/test_nodes/test_risk_check.py
"""Unit tests for risk check node"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
from nodes.risk_check_node import risk_check_node
from state.finance_state import create_initial_state


class TestRiskCheckNode(unittest.TestCase):
    """Test cases for risk check node"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = "test_user_001"
        # Mock is_off_hours to always return False to prevent time-of-day-dependent failures
        import nodes.risk_check_node
        self.original_is_off_hours = nodes.risk_check_node.is_off_hours
        nodes.risk_check_node.is_off_hours = lambda: False
        
    def tearDown(self):
        import nodes.risk_check_node
        nodes.risk_check_node.is_off_hours = self.original_is_off_hours
    
    def create_test_state(self, amount: float = None, recipient: str = None):
        """Create a test state with transaction details"""
        state = create_initial_state(self.user_id)
        if amount:
            state["transaction_amount"] = amount
        if recipient:
            state["recipient_account"] = recipient
        return state
    
    def test_low_risk_transaction(self):
        """Test low risk transaction scoring"""
        state = self.create_test_state(amount=100.00, recipient="known_friend")
        result = risk_check_node(state)
        
        self.assertLess(result["risk_score"], 30)
        self.assertFalse(result["needs_human_review"])
        self.assertFalse(result["fraud_flag"])
    
    def test_medium_risk_transaction(self):
        """Test medium risk transaction scoring"""
        state = self.create_test_state(amount=8000.00, recipient="new_recipient")
        result = risk_check_node(state)
        
        self.assertBetween(result["risk_score"], 30, 70)
        self.assertFalse(result["needs_human_review"])
    
    def test_high_risk_transaction(self):
        """Test high risk transaction scoring"""
        state = self.create_test_state(amount=15000.00, recipient="crypto_exchange")
        state["retry_count"] = 1
        result = risk_check_node(state)
        
        self.assertGreaterEqual(result["risk_score"], 70)
        self.assertTrue(result["needs_human_review"])
        self.assertTrue(result["fraud_flag"])
    
    def test_risk_factors_included(self):
        """Test that risk factors are included in result"""
        state = self.create_test_state(amount=25000.00, recipient="offshore_bank")
        result = risk_check_node(state)
        
        self.assertIn("risk_factors", result)
        self.assertGreater(len(result["risk_factors"]), 0)
    
    def test_multiple_risk_factors(self):
        """Test multiple risk factors combined"""
        state = self.create_test_state(amount=12000.00, recipient="new_crypto_account")
        result = risk_check_node(state)
        
        # Should trigger multiple risk factors
        risk_factors = result["risk_factors"]
        self.assertGreaterEqual(len(risk_factors), 2)
    
    def assertBetween(self, value, low, high):
        """Custom assertion to check value is between low and high"""
        self.assertGreaterEqual(value, low)
        self.assertLess(value, high)


if __name__ == "__main__":
    unittest.main()