# tests/test_tools/test_fraud_detection.py
"""Unit tests for fraud detection tool"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
from tools.fraud_detection import FraudDetectionTool


class TestFraudDetectionTool(unittest.TestCase):
    """Test cases for fraud detection tool"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tool = FraudDetectionTool()
        self.user_id = "test_user_001"
    
    def test_low_risk_transaction(self):
        """Test low risk transaction detection"""
        result = self.tool.execute(
            user_id=self.user_id,
            amount=50.00,
            recipient="trusted_friend"
        )
        
        self.assertLess(result["risk_score"], 30)
        self.assertEqual(result["fraud_level"], "low")
        self.assertEqual(result["recommendation"], "ALLOW_TRANSACTION")
    
    def test_medium_risk_transaction(self):
        """Test medium risk transaction detection"""
        result = self.tool.execute(
            user_id=self.user_id,
            amount=8000.00,
            recipient="new_vendor"
        )
        
        self.assertBetween(result["risk_score"], 30, 70)
        self.assertEqual(result["fraud_level"], "medium")
        self.assertEqual(result["recommendation"], "REQUIRE_REVIEW")
    
    def test_high_risk_transaction(self):
        """Test high risk transaction detection"""
        result = self.tool.execute(
            user_id=self.user_id,
            amount=50000.00,
            recipient="CRYPTO_EXCHANGE_XYZ"
        )
        
        self.assertGreaterEqual(result["risk_score"], 70)
        self.assertEqual(result["fraud_level"], "high")
        self.assertEqual(result["recommendation"], "BLOCK_TRANSACTION")
    
    def test_fraud_factors_included(self):
        """Test that fraud factors are included in result"""
        result = self.tool.execute(
            user_id=self.user_id,
            amount=25000.00,
            recipient="offshore_bank"
        )
        
        self.assertIn("risk_factors", result)
        self.assertGreater(len(result["risk_factors"]), 0)
    
    def test_crypto_recipient_flagged(self):
        """Test that crypto recipients are flagged"""
        crypto_recipients = ["Binance", "Coinbase", "Crypto Exchange", "Bitcoin Wallet"]
        
        for recipient in crypto_recipients:
            with self.subTest(recipient=recipient):
                result = self.tool.execute(
                    user_id=self.user_id,
                    amount=1000.00,
                    recipient=recipient
                )
                
                self.assertGreaterEqual(result["risk_score"], 50)
    
    def test_new_recipient_risk(self):
        """Test that new recipients add risk"""
        result_new = self.tool.execute(
            user_id=self.user_id,
            amount=500.00,
            recipient="completely_new_recipient_123"
        )
        
        result_known = self.tool.execute(
            user_id=self.user_id,
            amount=500.00,
            recipient="known_recipient"
        )
        
        self.assertGreater(result_new["risk_score"], result_known["risk_score"])
    
    def test_requires_human_review_flag(self):
        """Test that high risk triggers human review flag"""
        result = self.tool.execute(
            user_id=self.user_id,
            amount=100000.00,
            recipient="suspicious_account"
        )
        
        self.assertTrue(result["requires_human_review"])
    
    def test_transaction_blocking(self):
        """Test that very high risk transactions are blocked"""
        result = self.tool.execute(
            user_id=self.user_id,
            amount=200000.00,
            recipient="known_fraud_account"
        )
        
        self.assertTrue(result["is_blocked"])
    
    def assertBetween(self, value, low, high):
        """Custom assertion to check value is between low and high"""
        self.assertGreaterEqual(value, low)
        self.assertLess(value, high)


if __name__ == "__main__":
    unittest.main()