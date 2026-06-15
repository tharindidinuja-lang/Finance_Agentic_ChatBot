# tools/currency_converter.py
"""Currency conversion using real-time exchange rates"""

from tools.base_tool import BaseTool
from typing import Dict, Any
from datetime import datetime
import json
import os


class CurrencyConverterTool(BaseTool):
    """Convert between currencies using live exchange rates"""
    
    @property
    def name(self) -> str:
        return "convert_currency"
    
    @property
    def description(self) -> str:
        return "Convert an amount from one currency to another"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Amount to convert"
                },
                "from_currency": {
                    "type": "string",
                    "description": "Source currency code (USD, EUR, GBP, etc.)",
                    "minLength": 3,
                    "maxLength": 3
                },
                "to_currency": {
                    "type": "string",
                    "description": "Target currency code",
                    "minLength": 3,
                    "maxLength": 3
                }
            },
            "required": ["amount", "from_currency", "to_currency"]
        }
    
    def execute(self, amount: float, from_currency: str, to_currency: str, **kwargs) -> Dict[str, Any]:
        """Convert currency"""
        
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return {
                "success": True,
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted_amount": amount,
                "exchange_rate": 1.0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get exchange rate (simulated)
        exchange_rate = self._get_exchange_rate(from_currency, to_currency)
        converted_amount = amount * exchange_rate
        
        return {
            "success": True,
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": round(converted_amount, 2),
            "exchange_rate": exchange_rate,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_exchange_rate(self, from_curr: str, to_curr: str) -> float:
        """Get exchange rate (simulated - in production use API)"""
        
        # Sample exchange rates (base: USD)
        rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 151.50,
            "CAD": 1.37,
            "AUD": 1.52,
            "CHF": 0.91,
            "CNY": 7.24,
            "INR": 83.50,
            "BRL": 5.12,
        }
        
        if from_curr == "USD":
            return rates.get(to_curr, 1.0)
        elif to_curr == "USD":
            return 1.0 / rates.get(from_curr, 1.0)
        else:
            # Convert via USD
            usd_rate = 1.0 / rates.get(from_curr, 1.0)
            return usd_rate * rates.get(to_curr, 1.0)


# Test
if __name__ == "__main__":
    tool = CurrencyConverterTool()
    
    # Convert USD to EUR
    result = tool.execute(amount=1000.00, from_currency="USD", to_currency="EUR")
    print(f"${result['amount']:,.2f} {result['from_currency']} = ${result['converted_amount']:,.2f} {result['to_currency']}")
    print(f"Exchange rate: {result['exchange_rate']}")
    
    # Convert EUR to GBP
    result = tool.execute(amount=500.00, from_currency="EUR", to_currency="GBP")
    print(f"{result['amount']:,.2f} {result['from_currency']} = {result['converted_amount']:,.2f} {result['to_currency']}")