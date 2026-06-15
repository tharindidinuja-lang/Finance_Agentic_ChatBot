# main.py (Enhanced version)
"""Main entry point for Finance Agentic Chatbot CLI"""

from agents.finance_agent import create_finance_agent
from config.settings import get_settings
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_api_keys():
    """Check if required API keys are configured"""
    settings = get_settings()
    
    if not settings.openai_api_key:
        print("\n❌ ERROR: OPENAI_API_KEY not found in .env file")
        print("   Please copy .env.example to .env and add your API key")
        print("   Get your API key from: https://platform.openai.com/api-keys\n")
        return False
    return True


def print_welcome():
    """Print welcome message with version info"""
    settings = get_settings()
    
    print("=" * 60)
    print("🏦 FINANCE AGENTIC CHATBOT")
    print("=" * 60)
    print(f"Version: {settings.app_version}")
    print(f"LLM Model: {settings.openai_model}")
    print("-" * 60)
    print("Commands:")
    print("  • Type your banking questions directly")
    print("  • 'reset'    - Start fresh conversation")
    print("  • 'summary'  - Show conversation summary")
    print("  • 'history'  - Show transaction history")
    print("  • 'help'     - Show this help message")
    print("  • 'quit'     - Exit the application")
    print("=" * 60)
    print()


def print_help():
    """Print help message"""
    print("\n" + "-" * 50)
    print("Available Commands:")
    print("  reset     - Reset conversation (clear history)")
    print("  summary   - Show conversation summary")
    print("  history   - Show transaction history")
    print("  help      - Show this help message")
    print("  quit      - Exit the application")
    print("\nExample questions:")
    print("  • What's my checking account balance?")
    print("  • Transfer $500 to savings")
    print("  • What's Apple stock price?")
    print("  • Show my last 5 transactions")
    print("-" * 50 + "\n")


def show_history(agent, user_id: str):
    """Show transaction history"""
    from data import DataManager
    
    data_manager = DataManager()
    transactions = data_manager.get_transactions(user_id, limit=10)
    
    print("\n" + "=" * 50)
    print("📜 RECENT TRANSACTIONS")
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


def run_cli():
    """Run the finance agent in CLI mode"""
    
    # Check API keys first
    if not check_api_keys():
        sys.exit(1)
    
    print_welcome()
    
    try:
        # Create agent
        agent = create_finance_agent()
        user_id = "cli_user_001"
        
    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {e}")
        print("   Check your API key and internet connection.\n")
        sys.exit(1)
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            cmd = user_input.lower()
            
            if cmd == 'quit' or cmd == 'exit':
                print("\n👋 Thank you for using Finance Agent. Goodbye!\n")
                break
            
            elif cmd == 'reset':
                agent.reset_state(user_id)
                print("\n✅ Conversation reset successfully!\n")
                continue
            
            elif cmd == 'summary':
                summary = agent.get_conversation_summary(user_id)
                print("\n📊 CONVERSATION SUMMARY")
                print("=" * 40)
                if "error" in summary:
                    print(f"  ❌ {summary['error']}")
                else:
                    for key, value in summary.items():
                        if key != "last_interaction":
                            print(f"  • {key}: {value}")
                print("=" * 40 + "\n")
                continue
            
            elif cmd == 'history':
                show_history(agent, user_id)
                continue
            
            elif cmd == 'help':
                print_help()
                continue
            
            # Process through agent
            print("\n🤖 Agent: ", end="", flush=True)
            result = agent.process(user_input, user_id)
            
            # Display response
            print(f"{result['response']}")
            
            # Display additional info for demo
            risk_score = result.get('risk_score', 0)
            if risk_score > 70:
                print(f"\n⚠️  HIGH RISK ALERT: {risk_score}/100 - Transaction under review")
            elif risk_score > 50:
                print(f"\n⚠️  Medium Risk: {risk_score}/100")
            
            if result.get('needs_human_review'):
                print("🛑 Note: This transaction requires additional verification")
            
            if result.get('transaction_id'):
                print(f"📋 Transaction ID: {result['transaction_id']}")
            
            print()  # Empty line for readability
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("   Please try again or type 'reset' to start over.\n")


def run_demo():
    """Run a quick demo sequence"""
    
    print("\n🎬 Running Finance Agent Demo...\n")
    print("=" * 50)
    
    # Check API keys
    if not check_api_keys():
        return
    
    try:
        agent = create_finance_agent()
        user_id = "demo_user"
        
        demo_queries = [
            "What's my checking account balance?",
            "Transfer $100 to savings account",
            "What's Apple stock price?",
            "Show me my recent transactions"
        ]
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n📌 Demo {i}/{len(demo_queries)}")
            print(f"👤 User: {query}")
            print("🤖 Agent: ", end="", flush=True)
            
            result = agent.process(query, user_id)
            print(f"{result['response']}")
            
            if result.get('risk_score', 0) > 50:
                print(f"   ⚠️ Risk Score: {result['risk_score']}/100")
            
            print("-" * 40)
        
        print("\n✅ Demo complete!")
        print("\n💡 To start interactive mode, run: python main.py\n")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")


def show_banner():
    """Show ASCII banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     ███████╗██╗███╗   ██╗ █████╗ ███╗   ██╗ ██████╗███████╗  ║
    ║     ██╔════╝██║████╗  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝  ║
    ║     █████╗  ██║██╔██╗ ██║███████║██╔██╗ ██║██║     █████╗    ║
    ║     ██╔══╝  ██║██║╚██╗██║██╔══██║██║╚██╗██║██║     ██╔══╝    ║
    ║     ██║     ██║██║ ╚████║██║  ██║██║ ╚████║╚██████╗███████╗  ║
    ║     ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝  ║
    ║                                                              ║
    ║              Finance Agentic Chatbot - v1.0.0               ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            run_demo()
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("\nUsage: python main.py [OPTIONS]")
            print("\nOptions:")
            print("  --demo    Run demo sequence")
            print("  --help    Show this help message")
            print("\nExamples:")
            print("  python main.py          # Start interactive CLI")
            print("  python main.py --demo   # Run demo\n")
        elif sys.argv[1] == "--banner":
            show_banner()
        else:
            print(f"\n❌ Unknown option: {sys.argv[1]}")
            print("   Run 'python main.py --help' for usage\n")
    else:
        run_cli()