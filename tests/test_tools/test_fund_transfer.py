# tests/test_tools/test_fund_transfer.py
"""Unit tests for fund transfer tool"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
from tools.fund_transfer import FundTransferTool


class TestFundTransferTool(unittest.TestCase):
    """Test cases for fund transfer tool"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tool = FundTransferTool()
        self.user_id = "test_user_001"
    
    def test_successful_transfer(self):
        """Test successful fund transfer"""
        result = self.tool.execute(
            user_id=self.user_id,
            amount=500.00,
            to_account="SAVINGS_001",
            from_account="checking",
            description="Test transfer"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("transaction_id", result)
        self.assertEqual(result["amount"], 500.00)
        self.assertEqual(result["status"], "completed")
    
    def test_negative_amount_transfer(self):
        """Test transfer with negative amount (should fail)"""
        result = self.tool.execute(
            user_id=self.user_id,
            amount=-100.00,
            to_account="SAVINGS_001"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_zero_amount_transfer(self):
        """Test transfer with zero amount (should fail)"""
        result = self.tool.execute(
            user_id=self.user_id,
            amount=0.00,
            to_account="SAVINGS_001"
        )
        
        self.assertFalse(result["success"])
    
    def test_insufficient_funds(self):
        """Test transfer with insufficient funds"""
        # Try to transfer more than available
        result = self.tool.execute(
            user_id=self.user_id,
            amount=1000000.00,  # $1M - definitely insufficient
            to_account="SAVINGS_001"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("Insufficient funds", result.get("error", ""))
    
    def test_transaction_id_generation(self):
        """Test that transaction IDs are unique"""
        result1 = self.tool.execute(
            user_id=self.user_id,
            amount=100.00,
            to_account="ACC_001"
        )
        
        result2 = self.tool.execute(
            user_id=self.user_id,
            amount=200.00,
            to_account="ACC_002"
        )
        
        self.assertNotEqual(result1.get("transaction_id"), result2.get("transaction_id"))
    
    def test_transfer_with_description(self):
        """Test transfer with custom description"""
        description = "Monthly rent payment"
        result = self.tool.execute(
            user_id=self.user_id,
            amount=1500.00,
            to_account="LANDLORD_001",
            description=description
        )
        
        self.assertEqual(result.get("description"), description)
    
    def test_balance_update(self):
        """Test that balance is updated after transfer"""
        result = self.tool.execute(
            user_id=self.user_id,
            amount=250.00,
            to_account="SAVINGS_001"
        )
        
        self.assertIn("new_balance", result)
        self.assertIsInstance(result["new_balance"], float)


if __name__ == "__main__":
    unittest.main()