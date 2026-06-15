# ui/cli.py
"""Command-line interface for Finance Agentic Chatbot"""

import sys
import os
import json
from datetime import datetime
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.finance_agent import create_finance_agent
from config.settings import get_settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class FinanceAgentCLI:
    """Command-line interface for the Finance Agent"""
    
    def __init__(self):
        self.agent = create_finance_agent()
        self.user_id = "cli_user_001"
        self.running = True
        self.settings = get_settings()
    
    def run(self):
        """Run the CLI main loop"""
        self.print_welcome()
        
        while self.running:
            try:
                # Get user input
                user_input = self.get_user_input()
                
                if not user_input:
                    continue
                
                # Process command
                if user_input.startswith('/'):
                    self.handle_command(user_input)
                else:
                    self.process_message(user_input)
                    
            except KeyboardInterrupt:
                print("\n\n Goodbye!")
                break
            except Exception as e:
                print(f"\n Error: {e}")
                logger.error(f"CLI error: {e}")
    
    def print_welcome(self):
        """Print welcome message"""
        print("=" * 70)
        print(" FINANCE AGENTIC CHATBOT - Command Line Interface")
        print("=" * 70)
        print(f"Version: {self.settings.app_version}")
        print(f"Environment: {self.settings.app_env}")
        print(f"User ID: {self.user_id}")
        print("-" * 70)
        print("Commands:")
        print("  /help     - Show this help message")
        print("  /reset    - Reset conversation")
        print("  /summary  - Show conversation summary")
        print("  /metrics  - Show agent metrics")
        print("  /history  - Show transaction history")
        print("  /quit     - Exit the application")
        print("-" * 70)
        print("Type your banking questions below:\n")
    
    def get_user_input(self) -> Optional[str]:
        """Get user input with prompt"""
        try:
            user_input = input("You: ").strip()
            return user_input
        except EOFError:
            return "/quit"
    
    def process_message(self, message: str):
        """Process a user message"""
        print("\n Agent: ", end="", flush=True)
        
        # Process through agent
        result = self.agent.process(message, self.user_id)
        
        # Print response
        print(result["response"])
        
        # Print additional info for certain scenarios
        if result.get("risk_score", 0) > 50:
            print(f"\n  Risk Score: {result['risk_score']}/100 - Transaction under review")
        
        if result.get("needs_human_review"):
            print("\n This transaction requires human review. You will be notified.")
        
        if result.get("validation_status") == "failed":
            print("\n Transaction validation failed. Please check your input.")
        
        print()  # Empty line for readability
    
    def handle_command(self, command: str):
        """Handle slash commands"""
        cmd = command.lower()
        
        if cmd == "/help":
            self.print_help()
        
        elif cmd == "/reset":
            self.agent.reset_state(self.user_id)
            print("\n✅ Conversation reset successfully!\n")
        
        elif cmd == "/summary":
            self.show_summary()
        
        elif cmd == "/metrics":
            self.show_metrics()
        
        elif cmd == "/history":
            self.show_history()
        
        elif cmd == "/quit" or cmd == "/exit":
            self.running = False
            print("\n👋 Thank you for using Finance Agent. Goodbye!")
        
        else:
            print(f"\n❌ Unknown command: {command}\n")
            self.print_help()
    
    def print_help(self):
        """Print help message"""
        print("\n" + "-" * 50)
        print("Available Commands:")
        print("  /help     - Show this help message")
        print("  /reset    - Reset conversation (clear history)")
        print("  /summary  - Show conversation summary")
        print("  /metrics  - Show agent performance metrics")
        print("  /history  - Show transaction history")
        print("  /quit     - Exit the application")
        print("-" * 50 + "\n")
    
    def show_summary(self):
        """Show conversation summary"""
        summary = self.agent.get_conversation_summary(self.user_id)
        
        print("\n" + "=" * 50)
        print(" CONVERSATION SUMMARY")
        print("=" * 50)
        
        if "error" in summary:
            print(f" {summary['error']}")
        else:
            for key, value in summary.items():
                if key != "last_interaction":
                    print(f"  {key}: {value}")
        
        print("=" * 50 + "\n")
    
    def show_metrics(self):
        """Show agent metrics"""
        metrics = self.agent.get_agent_metrics()
        
        print("\n" + "=" * 50)
        print("AGENT METRICS")
        print("=" * 50)
        print(f"  Agent Name: {metrics['agent_name']}")
        print(f"  Total Messages: {metrics['total_messages']}")
        print(f"  Total Errors: {metrics['total_errors']}")
        print(f"  Error Rate: {metrics['error_rate']:.2%}")
        print(f"  Active Users: {metrics['active_users']}")
        print(f"  Created At: {metrics['created_at']}")
        print("=" * 50 + "\n")
    
    def show_history(self):
        """Show transaction history"""
        from data import DataManager
        
        data_manager = DataManager()
        transactions = data_manager.get_transactions(self.user_id, limit=10)
        
        print("\n" + "=" * 50)
        print(" RECENT TRANSACTIONS")
        print("=" * 50)
        
        if not transactions:
            print("  No transactions found.")
        else:
            for tx in transactions:
                amount = tx.get("amount", 0)
                tx_type = tx.get("type", "unknown")
                description = tx.get("description", "No description")
                date = tx.get("date", tx.get("timestamp", "Unknown"))[:10]
                
                if tx_type in ["credit", "deposit"]:
                    print(f"  {date}: +${amount:,.2f} - {description}")
                else:
                    print(f"  {date}: -${amount:,.2f} - {description}")
        
        print("=" * 50 + "\n")


def main():
    """Entry point for CLI"""
    cli = FinanceAgentCLI()
    cli.run()


if __name__ == "__main__":
    main()