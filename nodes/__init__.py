# tools/__init__.py
"""Financial tools for agentic chatbot"""

from tools.base_tool import BaseTool
from tools.account_balance import AccountBalanceTool
from tools.transaction_history import TransactionHistoryTool
from tools.stock_price import StockPriceTool
from tools.fund_transfer import FundTransferTool
from tools.fraud_detection import FraudDetectionTool
from tools.investment_portfolio import InvestmentPortfolioTool
from tools.currency_converter import CurrencyConverterTool
from tools.loan_calculator import LoanCalculatorTool
from tools.credit_score import CreditScoreTool

# Registry of all available tools
TOOL_REGISTRY = {
    "get_account_balance": AccountBalanceTool,
    "get_transaction_history": TransactionHistoryTool,
    "fetch_stock_price": StockPriceTool,
    "execute_fund_transfer": FundTransferTool,
    "detect_fraud": FraudDetectionTool,
    "get_portfolio": InvestmentPortfolioTool,
    "convert_currency": CurrencyConverterTool,
    "calculate_loan": LoanCalculatorTool,
    "get_credit_score": CreditScoreTool,
}

def get_tool(tool_name: str):
    """Get a tool instance by name"""
    tool_class = TOOL_REGISTRY.get(tool_name)
    if tool_class:
        return tool_class()
    return None

def list_available_tools():
    """List all available tool names"""
    return list(TOOL_REGISTRY.keys())

__all__ = [
    "BaseTool",
    "AccountBalanceTool",
    "TransactionHistoryTool", 
    "StockPriceTool",
    "FundTransferTool",
    "FraudDetectionTool",
    "InvestmentPortfolioTool",
    "CurrencyConverterTool",
    "LoanCalculatorTool",
    "CreditScoreTool",
    "TOOL_REGISTRY",
    "get_tool",
    "list_available_tools",
]