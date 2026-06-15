# tests/test_nodes/test_classifier.py
"""Unit tests for classifier node"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
from nodes.classifier_node import classifier_node
from state.finance_state import create_initial_state


class TestClassifierNode(unittest.TestCase):
    """Test cases for classifier node"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = "test_user_001"
    
    def create_test_state(self, user_message: str):
        """Create a test state with user message"""
        state = create_initial_state(self.user_id)
        state["messages"].append({"role": "user", "content": user_message})
        return state
    
    def test_classify_balance_check(self):
        """Test balance check intent classification"""
        test_messages = [
            "What's my account balance?",
            "How much money do I have?",
            "Show me my checking balance",
            "What is my current balance?"
        ]
        
        for message in test_messages:
            with self.subTest(message=message):
                state = self.create_test_state(message)
                result = classifier_node(state)
                self.assertEqual(result["intent"], "balance_check")
    
    def test_classify_transfer(self):
        """Test transfer intent classification"""
        test_messages = [
            "Transfer $500 to savings",
            "Send money to John",
            "Move funds to checking",
            "Pay $100 to credit card"
        ]
        
        for message in test_messages:
            with self.subTest(message=message):
                state = self.create_test_state(message)
                result = classifier_node(state)
                self.assertEqual(result["intent"], "transfer_money")
    
    def test_classify_stock_price(self):
        """Test stock price intent classification"""
        test_messages = [
            "What's Apple stock price?",
            "Show me TSLA stock",
            "How is Microsoft stock doing?",
            "Get current market price for AAPL"
        ]
        
        for message in test_messages:
            with self.subTest(message=message):
                state = self.create_test_state(message)
                result = classifier_node(state)
                self.assertEqual(result["intent"], "stock_price")
    
    def test_classify_fraud_report(self):
        """Test fraud report intent classification"""
        test_messages = [
            "I think someone hacked my account",
            "Report fraudulent transaction",
            "Unauthorized charge on my card",
            "Suspicious activity detected"
        ]
        
        for message in test_messages:
            with self.subTest(message=message):
                state = self.create_test_state(message)
                result = classifier_node(state)
                self.assertEqual(result["intent"], "fraud_report")
    
    def test_classify_general_query(self):
        """Test general query classification"""
        test_messages = [
            "Hello, how are you?",
            "What services do you offer?",
            "Thank you for your help",
            "I need assistance"
        ]
        
        for message in test_messages:
            with self.subTest(message=message):
                state = self.create_test_state(message)
                result = classifier_node(state)
                self.assertEqual(result["intent"], "general_query")
    
    def test_classify_extracts_entities(self):
        """Test entity extraction from messages"""
        state = self.create_test_state("Transfer $750 to account #123456789")
        result = classifier_node(state)
        
        # Check that entities were extracted
        self.assertIn("extracted_entities", result)
        self.assertEqual(result["extracted_entities"].get("amount"), 750.0)
        self.assertEqual(result["extracted_entities"].get("recipient"), "123456789")


if __name__ == "__main__":
    unittest.main()