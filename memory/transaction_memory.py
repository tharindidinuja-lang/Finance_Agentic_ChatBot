# memory/transaction_memory.py
"""Store and manage transaction history per user"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
import os


class TransactionMemory:
    """
    Stores transaction history for each user.
    Supports filtering by date, amount, and type.
    """
    
    def __init__(self, persistence_dir: str = "data/transactions"):
        """
        Initialize transaction memory.
        
        Args:
            persistence_dir: Directory to store transaction data
        """
        self.persistence_dir = persistence_dir
        os.makedirs(persistence_dir, exist_ok=True)
        
        # In-memory cache: user_id -> list of transactions
        self.transactions: Dict[str, List[Dict]] = defaultdict(list)
        
        # Load existing transactions
        self._load_all_transactions()
    
    def add_transaction(self, user_id: str, transaction: Dict) -> str:
        """
        Add a transaction to user's history.
        
        Args:
            user_id: User identifier
            transaction: Transaction details (amount, type, recipient, etc.)
            
        Returns:
            Transaction ID
        """
        # Ensure transaction has required fields
        if "transaction_id" not in transaction:
            transaction["transaction_id"] = self._generate_transaction_id(user_id)
        
        if "timestamp" not in transaction:
            transaction["timestamp"] = datetime.now().isoformat()
        
        if "status" not in transaction:
            transaction["status"] = "completed"
        
        # Add to memory
        self.transactions[user_id].append(transaction)
        
        # Keep only last 100 transactions per user (for memory efficiency)
        if len(self.transactions[user_id]) > 100:
            self.transactions[user_id] = self.transactions[user_id][-100:]
        
        # Persist to disk
        self._save_user_transactions(user_id)
        
        return transaction["transaction_id"]
    
    def get_transactions(self, user_id: str, 
                        limit: int = 10,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        min_amount: Optional[float] = None,
                        max_amount: Optional[float] = None,
                        transaction_type: Optional[str] = None) -> List[Dict]:
        """
        Get filtered transactions for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of transactions to return
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            min_amount: Minimum transaction amount
            max_amount: Maximum transaction amount
            transaction_type: Filter by type ('transfer', 'deposit', 'withdrawal')
            
        Returns:
            List of filtered transactions
        """
        if user_id not in self.transactions:
            return []
        
        transactions = self.transactions[user_id][::-1]  # Most recent first
        
        # Apply filters
        filtered = []
        for tx in transactions:
            # Date filter
            if start_date and tx["timestamp"] < start_date:
                continue
            if end_date and tx["timestamp"] > end_date:
                continue
            
            # Amount filter
            amount = tx.get("amount", 0)
            if min_amount and amount < min_amount:
                continue
            if max_amount and amount > max_amount:
                continue
            
            # Type filter
            if transaction_type and tx.get("type") != transaction_type:
                continue
            
            filtered.append(tx)
            
            if len(filtered) >= limit:
                break
        
        return filtered
    
    def get_recent_transactions(self, user_id: str, hours: int = 24) -> List[Dict]:
        """
        Get transactions from the last N hours.
        
        Args:
            user_id: User identifier
            hours: Number of hours to look back
            
        Returns:
            List of recent transactions
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_iso = cutoff_time.isoformat()
        
        return self.get_transactions(user_id, start_date=cutoff_iso, limit=50)
    
    def get_total_spent(self, user_id: str, days: int = 30) -> float:
        """
        Calculate total amount spent (outgoing transfers) in last N days.
        
        Args:
            user_id: User identifier
            days: Number of days to look back
            
        Returns:
            Total amount spent
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        transactions = self.get_transactions(
            user_id, 
            start_date=cutoff_date,
            transaction_type="transfer"
        )
        
        total = sum(tx.get("amount", 0) for tx in transactions)
        return total
    
    def get_transaction_by_id(self, user_id: str, transaction_id: str) -> Optional[Dict]:
        """
        Get a specific transaction by ID.
        
        Args:
            user_id: User identifier
            transaction_id: Transaction identifier
            
        Returns:
            Transaction dict or None
        """
        for tx in self.transactions.get(user_id, []):
            if tx.get("transaction_id") == transaction_id:
                return tx
        return None
    
    def update_transaction_status(self, user_id: str, transaction_id: str, status: str):
        """
        Update transaction status (e.g., 'pending' -> 'completed').
        
        Args:
            user_id: User identifier
            transaction_id: Transaction identifier
            status: New status ('pending', 'completed', 'failed', 'cancelled')
        """
        for tx in self.transactions.get(user_id, []):
            if tx.get("transaction_id") == transaction_id:
                tx["status"] = status
                tx["updated_at"] = datetime.now().isoformat()
                self._save_user_transactions(user_id)
                break
    
    def get_daily_velocity(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate transaction velocity for fraud detection.
        
        Returns:
            Dictionary with counts and amounts per day
        """
        today = datetime.now().date()
        daily_total = 0
        daily_count = 0
        hourly_count = 0
        
        # Get last 24 hours of transactions
        recent = self.get_recent_transactions(user_id, hours=24)
        
        for tx in recent:
            tx_date = datetime.fromisoformat(tx["timestamp"]).date()
            if tx_date == today:
                daily_total += tx.get("amount", 0)
                daily_count += 1
            
            # Check last hour
            tx_time = datetime.fromisoformat(tx["timestamp"])
            if (datetime.now() - tx_time).seconds < 3600:
                hourly_count += 1
        
        return {
            "daily_transaction_count": daily_count,
            "daily_total_amount": daily_total,
            "hourly_transaction_count": hourly_count,
            "is_high_velocity": daily_count > 10 or hourly_count > 5
        }
    
    def clear_user_history(self, user_id: str):
        """Clear all transactions for a user."""
        if user_id in self.transactions:
            del self.transactions[user_id]
            self._delete_user_file(user_id)
    
    def _generate_transaction_id(self, user_id: str) -> str:
        """Generate unique transaction ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"TXN_{user_id}_{timestamp}_{len(self.transactions.get(user_id, []))}"
    
    def _save_user_transactions(self, user_id: str):
        """Save user transactions to disk."""
        filepath = os.path.join(self.persistence_dir, f"{user_id}.json")
        try:
            with open(filepath, 'w') as f:
                json.dump(self.transactions[user_id], f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving transactions for {user_id}: {e}")
    
    def _load_all_transactions(self):
        """Load all user transactions from disk."""
        if os.path.exists(self.persistence_dir):
            for filename in os.listdir(self.persistence_dir):
                if filename.endswith('.json'):
                    user_id = filename[:-5]  # Remove .json
                    filepath = os.path.join(self.persistence_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            self.transactions[user_id] = json.load(f)
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
    
    def _delete_user_file(self, user_id: str):
        """Delete user transaction file."""
        filepath = os.path.join(self.persistence_dir, f"{user_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
    
    def get_summary(self, user_id: str) -> Dict[str, Any]:
        """Get transaction summary for a user."""
        transactions = self.transactions.get(user_id, [])
        
        if not transactions:
            return {"error": "No transactions found"}
        
        completed = [t for t in transactions if t.get("status") == "completed"]
        total_transferred = sum(t.get("amount", 0) for t in completed if t.get("type") == "transfer")
        
        return {
            "total_transactions": len(transactions),
            "completed_transactions": len(completed),
            "failed_transactions": len([t for t in transactions if t.get("status") == "failed"]),
            "total_amount_transferred": total_transferred,
            "avg_transaction_amount": total_transferred / len(completed) if completed else 0,
            "last_transaction": transactions[-1] if transactions else None
        }


# Test the transaction memory
if __name__ == "__main__":
    print("="*60)
    print("Transaction Memory Test")
    print("="*60)
    
    # Create memory
    memory = TransactionMemory(persistence_dir="data/test_transactions")
    
    user_id = "test_user_001"
    
    # Add some transactions
    memory.add_transaction(user_id, {
        "type": "transfer",
        "amount": 500.00,
        "recipient": "SAVINGS_001",
        "description": "Monthly savings transfer"
    })
    
    memory.add_transaction(user_id, {
        "type": "transfer", 
        "amount": 1500.00,
        "recipient": "BILL_PAY",
        "description": "Rent payment"
    })
    
    memory.add_transaction(user_id, {
        "type": "deposit",
        "amount": 3000.00,
        "source": "DIRECT_DEPOSIT",
        "description": "Salary deposit"
    })
    
    # Get recent transactions
    print("\nRecent Transactions:")
    for tx in memory.get_transactions(user_id, limit=5):
        print(f"  ${tx['amount']} - {tx.get('description', 'No description')} ({tx['status']})")
    
    # Get velocity check
    print("\nVelocity Check:")
    velocity = memory.get_daily_velocity(user_id)
    for key, value in velocity.items():
        print(f"  {key}: {value}")
    
    # Get summary
    print("\nTransaction Summary:")
    summary = memory.get_summary(user_id)
    for key, value in summary.items():
        if key != "last_transaction":
            print(f"  {key}: {value}")