# tools/investment_portfolio.py
"""Get investment portfolio holdings and performance"""

from tools.base_tool import BaseTool
from typing import Dict, Any, List
from datetime import datetime


class InvestmentPortfolioTool(BaseTool):
    """Get user's investment portfolio details"""
    
    @property
    def name(self) -> str:
        return "get_portfolio"
    
    @property
    def description(self) -> str:
        return "Get user's investment portfolio holdings, values, and performance"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier"
                },
                "include_history": {
                    "type": "boolean",
                    "description": "Include historical performance",
                    "default": False
                }
            },
            "required": ["user_id"]
        }
    
    def execute(self, user_id: str, include_history: bool = False, **kwargs) -> Dict[str, Any]:
        """Get portfolio data"""
        
        portfolio = self._get_simulated_portfolio(user_id)
        
        # Calculate totals
        total_value = sum(h["value"] for h in portfolio["holdings"])
        total_cost = sum(h["cost_basis"] for h in portfolio["holdings"])
        total_gain_loss = total_value - total_cost
        total_return_pct = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "success": True,
            "user_id": user_id,
            "holdings": portfolio["holdings"],
            "summary": {
                "total_value": total_value,
                "total_cost_basis": total_cost,
                "total_gain_loss": total_gain_loss,
                "total_return_percentage": total_return_pct,
                "number_of_positions": len(portfolio["holdings"]),
                "last_updated": datetime.now().isoformat()
            },
            "historical_performance": portfolio.get("history", []) if include_history else None
        }
    
    def _get_simulated_portfolio(self, user_id: str) -> Dict:
        """Generate simulated portfolio data"""
        
        holdings = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "shares": 50,
                "avg_price": 150.00,
                "current_price": 175.50,
                "value": 8775.00,
                "cost_basis": 7500.00,
                "gain_loss": 1275.00,
                "return_pct": 17.00,
                "allocation_pct": 35.2
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corp",
                "shares": 25,
                "avg_price": 380.00,
                "current_price": 420.75,
                "value": 10518.75,
                "cost_basis": 9500.00,
                "gain_loss": 1018.75,
                "return_pct": 10.72,
                "allocation_pct": 42.2
            },
            {
                "symbol": "VOO",
                "name": "Vanguard S&P 500 ETF",
                "shares": 30,
                "avg_price": 425.00,
                "current_price": 450.30,
                "value": 13509.00,
                "cost_basis": 12750.00,
                "gain_loss": 759.00,
                "return_pct": 5.95,
                "allocation_pct": 22.6
            }
        ]
        
        return {
            "holdings": holdings,
            "history": []  # Would contain historical values
        }


# Test
if __name__ == "__main__":
    tool = InvestmentPortfolioTool()
    result = tool.execute(user_id="user_123")
    
    print(f"Portfolio Summary:")
    print(f"  Total Value: ${result['summary']['total_value']:,.2f}")
    print(f"  Total Return: ${result['summary']['total_gain_loss']:,.2f}")
    print(f"  Return %: {result['summary']['total_return_percentage']:.2f}%")
    print(f"\nHoldings:")
    for holding in result['holdings']:
        print(f"  {holding['symbol']}: {holding['shares']} shares @ ${holding['current_price']} = ${holding['value']:,.2f}")