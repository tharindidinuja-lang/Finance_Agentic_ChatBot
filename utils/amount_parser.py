# utils/amount_parser.py
"""Parse monetary amounts from natural language"""

import re
from typing import Optional, Tuple, Dict, Any, List
from decimal import Decimal, InvalidOperation


class AmountParser:
    """
    Parse monetary amounts from various text formats.
    Supports: "$1,000.50", "1000 dollars", "five hundred", etc.
    """
    
    # Word to number mapping
    WORD_NUMBERS = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
        "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
        "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
        "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000,
        "million": 1000000, "billion": 1000000000
    }
    
    # Currency symbols
    CURRENCY_SYMBOLS = {
        "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR",
        "CAD": "CAD", "AUD": "AUD", "CHF": "CHF", "CNY": "CNY"
    }
    
    def __init__(self):
        self.currency_detected = "USD"
    
    def parse(self, text: str) -> Optional[float]:
        """
        Parse amount from text.
        
        Args:
            text: Input text (e.g., "$1,000.50" or "five hundred dollars")
            
        Returns:
            Parsed amount as float, or None if not found
        """
        # Try numeric patterns first
        amount = self.parse_numeric(text)
        if amount is not None:
            return amount
        
        # Try word-based parsing
        amount = self.parse_words(text)
        if amount is not None:
            return amount
        
        return None
    
    def parse_numeric(self, text: str) -> Optional[float]:
        """
        Parse numeric amount patterns.
        Supports: $1,000.50, 1000.50, 1,000, 1000 dollars
        """
        patterns = [
            # Currency symbol followed by number: $1,000.50
            r'[$€£¥₹]\s*([\d,]+(?:\.\d{2})?)',
            
            # Number followed by currency: 1000 dollars
            r'([\d,]+(?:\.\d{2})?)\s*(?:dollars?|USD|usd)',
            
            # Just a number (with possible commas and decimals)
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    
                    # Detect currency
                    if '$' in match.group(0) or 'dollar' in match.group(0).lower():
                        self.currency_detected = "USD"
                    
                    return amount
                except ValueError:
                    continue
        
        return None
    
    def parse_words(self, text: str) -> Optional[float]:
        """
        Parse word-based amounts.
        Supports: "five hundred dollars", "one thousand fifty"
        """
        # Convert to lowercase and remove currency words
        text_lower = text.lower()
        
        # Remove currency indicators
        for currency in ["dollars", "usd", "cents"]:
            text_lower = text_lower.replace(currency, "")
        
        # Extract number words
        words = re.findall(r'\b(?:' + '|'.join(self.WORD_NUMBERS.keys()) + r')\b', text_lower)
        
        if not words:
            return None
        
        total = 0
        current = 0
        
        for word in words:
            value = self.WORD_NUMBERS[word]
            
            if value >= 1000:  # thousand, million, billion
                if current == 0:
                    current = 1
                total += current * value
                current = 0
            elif value >= 100:  # hundred
                if current == 0:
                    current = 1
                current *= value
            else:
                current += value
        
        total += current
        
        return float(total) if total > 0 else None
    
    def parse_with_currency(self, text: str) -> Tuple[Optional[float], str]:
        """
        Parse amount and detect currency.
        
        Returns:
            Tuple of (amount, currency_code)
        """
        amount = self.parse(text)
        return amount, self.currency_detected
    
    def parse_all_amounts(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse all amounts found in text.
        
        Returns:
            List of dicts with amount, currency, and position
        """
        amounts = []
        
        # Find all numeric patterns with positions
        patterns = [
            (r'[$€£¥₹]\s*([\d,]+(?:\.\d{2})?)', 'symbol'),
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|USD)', 'word'),
        ]
        
        for pattern, ptype in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    
                    # Detect currency
                    if '$' in match.group(0) or 'dollar' in match.group(0).lower():
                        currency = "USD"
                    elif '€' in match.group(0) or 'euro' in match.group(0).lower():
                        currency = "EUR"
                    elif '£' in match.group(0) or 'pound' in match.group(0).lower():
                        currency = "GBP"
                    else:
                        currency = "USD"
                    
                    amounts.append({
                        "amount": amount,
                        "currency": currency,
                        "original": match.group(0),
                        "start": match.start(),
                        "end": match.end()
                    })
                except ValueError:
                    continue
        
        return amounts
    
    def format_amount(self, amount: float, currency: str = "USD", 
                      include_symbol: bool = True) -> str:
        """
        Format amount for display.
        
        Args:
            amount: Numeric amount
            currency: Currency code (USD, EUR, GBP)
            include_symbol: Include currency symbol
            
        Returns:
            Formatted string (e.g., "$1,000.50")
        """
        currency_symbols = {
            "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹"
        }
        
        # Format with commas and 2 decimals
        formatted = f"{amount:,.2f}"
        
        if include_symbol:
            symbol = currency_symbols.get(currency, "$")
            return f"{symbol}{formatted}"
        else:
            return f"{formatted} {currency}"
    
    def validate_amount(self, amount: float, min_amount: float = 0.01, 
                        max_amount: float = 1000000) -> Tuple[bool, Optional[str]]:
        """
        Validate amount against business rules.
        
        Args:
            amount: Amount to validate
            min_amount: Minimum allowed amount
            max_amount: Maximum allowed amount
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if amount <= 0:
            return False, "Amount must be greater than zero"
        
        if amount < min_amount:
            return False, f"Minimum transfer amount is ${min_amount:,.2f}"
        
        if amount > max_amount:
            return False, f"Maximum transfer amount is ${max_amount:,.2f}"
        
        # Check for reasonable decimal places
        decimal_places = len(str(amount).split('.')[-1]) if '.' in str(amount) else 0
        if decimal_places > 2:
            return False, "Amount cannot have more than 2 decimal places"
        
        return True, None


# Convenience functions
def parse_amount(text: str) -> Optional[float]:
    """Quick parse amount from text"""
    parser = AmountParser()
    return parser.parse(text)


def format_money(amount: float, currency: str = "USD") -> str:
    """Quick format money"""
    parser = AmountParser()
    return parser.format_amount(amount, currency)


if __name__ == "__main__":
    print("=" * 50)
    print("AMOUNT PARSER TEST")
    print("=" * 50)
    
    parser = AmountParser()
    
    test_cases = [
        "$1,000.50",
        "transfer 500 dollars",
        "five hundred dollars",
        "one thousand fifty",
        "€100",
        "send $2,000",
        "pay 1,000.00 USD",
        "two hundred fifty",
    ]
    
    print("\nParsing Results:")
    for test in test_cases:
        amount = parser.parse(test)
        print(f"  '{test}' → ${amount:,.2f}" if amount else f"  '{test}' → None")
    
    # Test multiple amounts
    text = "Send $500 to John and $1,000 to Mary"
    amounts = parser.parse_all_amounts(text)
    print(f"\nMultiple amounts in '{text}':")
    for a in amounts:
        print(f"  {a['original']} → ${a['amount']:,.2f}")
    
    # Test validation
    print("\nValidation Tests:")
    valid, error = parser.validate_amount(100.00)
    print(f"  $100.00 → Valid: {valid}")
    
    valid, error = parser.validate_amount(-50.00)
    print(f"  -$50.00 → Valid: {valid}, Error: {error}")
    
    valid, error = parser.validate_amount(100.001)
    print(f"  $100.001 → Valid: {valid}, Error: {error}")
    
    # Test formatting
    print("\nFormatting:")
    print(f"  {parser.format_amount(1234.56)}")
    print(f"  {parser.format_amount(1234.56, 'EUR')}")
    print(f"  {parser.format_amount(1234.56, include_symbol=False)}")