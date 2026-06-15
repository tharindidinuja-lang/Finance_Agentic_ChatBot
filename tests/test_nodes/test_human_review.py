# tests/test_nodes/test_human_review.py
"""Unit tests for human review node"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
from unittest.mock import patch
from nodes.human_review_node import human_review_node
from state.finance_state import create_initial_state


class TestHumanReviewNode(unittest.TestCase):
    """Test cases for human review node"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = "test_user_001"
    
    def create_test_state(self, needs_review: bool = True, risk_score: int = 75):
        """Create a test state for human review"""
        state = create_initial_state(self.user_id)
        state["needs_human_review"] = needs_review
        state["risk_score"] = risk_score
        state["transaction_amount"] = 15000.00
        state["recipient_account"] = "NEW_ACCOUNT_123"
        return state
    
    @patch('builtins.input', return_value='yes')
    def test_approve_transaction(self, mock_input):
        """Test transaction approval by human reviewer"""
        state = self.create_test_state(needs_review=True)
        result = human_review_node(state)
        
        self.assertTrue(result["human_approved"])
        self.assertEqual(result["human_review_decision"], "approved")
    
    @patch('builtins.input', return_value='no')
    def test_deny_transaction(self, mock_input):
        """Test transaction denial by human reviewer"""
        state = self.create_test_state(needs_review=True)
        result = human_review_node(state)
        
        self.assertFalse(result["human_approved"])
        self.assertEqual(result["human_review_decision"], "denied")
    
    @patch('builtins.input', side_effect=['modify', '12000'])
    def test_modify_transaction(self, mock_input):
        """Test transaction modification by human reviewer"""
        state = self.create_test_state(needs_review=True)
        state["transaction_amount"] = 15000.00
        result = human_review_node(state)
        
        self.assertTrue(result["human_approved"])
        self.assertEqual(result["human_review_decision"], "modified")
        self.assertEqual(result["transaction_amount"], 12000.00)
    
    def test_skip_review_when_not_needed(self):
        """Test that review is skipped when not needed"""
        state = self.create_test_state(needs_review=False, risk_score=20)
        result = human_review_node(state)
        
        self.assertTrue(result["human_approved"])  # Auto-approved
        self.assertEqual(result.get("human_review_decision"), "pending")
    
    def test_human_review_logging(self):
        """Test that human review is logged"""
        with patch('builtins.input', return_value='yes'):
            state = self.create_test_state(needs_review=True)
            result = human_review_node(state)
            
            # Check that review was logged
            self.assertIsNotNone(result.get("human_review_notes"))


if __name__ == "__main__":
    unittest.main()