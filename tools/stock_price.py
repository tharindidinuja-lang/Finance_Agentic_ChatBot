# tools/stock_price.py
"""Real-time stock price fetching"""

from tools.base_tool import BaseTool
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
import random


class StockPriceTool(BaseTool):
    """Get current stock price and market data"""
    
    @property
    def name(self) -> str:
        return "fetch_stock_price"
    
    @property
    def description(self) -> str:
        return "Get current stock price, change, and volume for a given symbol"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)"
                }
            },
            "required": ["symbol"]
        }
    
    def execute(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Fetch stock price for given symbol"""
        
        # In production, use yfinance or Alpha Vantage API
        # For demo, return simulated data
        
        stock_data = self._get_simulated_stock_data(symbol.upper())
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "price": stock_data["price"],
            "change": stock_data["change"],
            "change_percent": stock_data["change_percent"],
            "volume": stock_data["volume"],
            "day_high": stock_data["day_high"],
            "day_low": stock_data["day_low"],
            "timestamp": datetime.now().isoformat(),
            "currency": "USD"
        }
    
    def _get_simulated_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Generate simulated stock data"""
        
        # Sample stock database
        stock_prices = {
            "AAPL": {"price": 175.50, "change": 2.30, "change_percent": 1.33, "volume": 55000000, "day_high": 176.20, "day_low": 173.80},
            "GOOGL": {"price": 138.25, "change": -1.15, "change_percent": -0.82, "volume": 22000000, "day_high": 139.50, "day_low": 137.90},
            "MSFT": {"price": 420.75, "change": 5.20, "change_percent": 1.25, "volume": 31000000, "day_high": 422.50, "day_low": 418.30},
            "TSLA": {"price": 245.30, "change": -8.50, "change_percent": -3.35, "volume": 98000000, "day_high": 252.80, "day_low": 243.20},
            "AMZN": {"price": 145.80, "change": 1.40, "change_percent": 0.97, "volume": 45000000, "day_high": 146.50, "day_low": 144.90},
            "META": {"price": 325.60, "change": 4.20, "change_percent": 1.31, "volume": 28000000, "day_high": 327.30, "day_low": 322.80},
            "NVDA": {"price": 895.20, "change": 15.30, "change_percent": 1.74, "volume": 62000000, "day_high": 900.50, "day_low": 888.00},
            "JPM": {"price": 198.45, "change": -2.10, "change_percent": -1.05, "volume": 15000000, "day_high": 200.20, "day_low": 197.80},
            "V": {"price": 275.30, "change": 3.40, "change_percent": 1.25, "volume": 12000000, "day_high": 276.50, "day_low": 273.80},
            "WMT": {"price": 60.75, "change": 0.25, "change_percent": 0.41, "volume": 18000000, "day_high": 61.20, "day_low": 60.40},
        }
        
        if symbol in stock_prices:
            return stock_prices[symbol]
        else:
            # Return random data for unknown symbols
            base_price = random.uniform(50, 500)
            change = random.uniform(-10, 10)
            return {
                "price": round(base_price, 2),
                "change": round(change, 2),
                "change_percent": round((change / base_price) * 100, 2),
                "volume": random.randint(1000000, 100000000),
                "day_high": round(base_price + random.uniform(0, 10), 2),
                "day_low": round(base_price - random.uniform(0, 10), 2),
            }


# Test
if __name__ == "__main__":
    tool = StockPriceTool()
    for symbol in ["AAPL", "GOOGL", "TSLA"]:
        result = tool.execute(symbol=symbol)
        print(f"{result['symbol']}: ${result['price']} ({result['change_percent']:+.2f}%)")