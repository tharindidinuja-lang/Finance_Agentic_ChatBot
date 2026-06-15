# utils/token_counter.py
"""Token counting and budgeting utilities for LLM calls"""

import re
from typing import List, Dict, Any, Optional
from collections import Counter


class TokenCounter:
    """
    Token counter for LLM budget management.
    Uses approximate counting (1 token ≈ 4 chars for English).
    For production, use tiktoken for OpenAI models.
    """
    
    # Approximate tokens per character by language
    TOKENS_PER_CHAR = {
        "english": 0.25,  # 4 chars per token
        "code": 0.3,      # Code is more dense
        "numbers": 0.2,   # Numbers tokenize efficiently
    }
    
    # Token limits by model
    MODEL_LIMITS = {
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-3.5-turbo": 16384,
        "claude-3-opus": 200000,
        "claude-3-sonnet": 200000,
        "llama-3-70b": 8192,
    }
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.max_tokens = self.MODEL_LIMITS.get(model_name, 128000)
        self.reset()
    
    def reset(self):
        """Reset token counters"""
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.call_count = 0
    
    def count_text(self, text: str, language: str = "english") -> int:
        """
        Count tokens in a text string.
        
        Args:
            text: Input text
            language: Language type ('english', 'code', 'numbers')
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        # Count characters
        char_count = len(text)
        
        # Get tokens per char rate
        rate = self.TOKENS_PER_CHAR.get(language, 0.25)
        
        # Estimate tokens
        estimated_tokens = int(char_count * rate)
        
        # Add overhead for special characters
        special_chars = len(re.findall(r'[{}()<>\[\]@#$%^&*]', text))
        estimated_tokens += special_chars // 4
        
        return max(1, estimated_tokens)
    
    def count_messages(self, messages: List[Dict[str, str]]) -> int:
        """
        Count tokens in a list of messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Total token count
        """
        total = 0
        
        for msg in messages:
            # Count content
            content = msg.get("content", "")
            total += self.count_text(content)
            
            # Add overhead for role and formatting
            total += 4  # ~4 tokens for role and formatting
            
            # Add overhead for function calls if present
            if "function_call" in msg:
                total += self.count_text(str(msg["function_call"]), "code")
        
        return total
    
    def count_tool_calls(self, tools: List[Dict[str, Any]]) -> int:
        """
        Count tokens in tool definitions.
        
        Args:
            tools: List of tool definitions
            
        Returns:
            Token count for tool definitions
        """
        if not tools:
            return 0
        
        total = 0
        for tool in tools:
            total += self.count_text(str(tool), "code")
        
        return total
    
    def check_budget(self, input_tokens: int, output_tokens: int = 1000) -> bool:
        """
        Check if token usage is within budget.
        
        Args:
            input_tokens: Tokens for input
            output_tokens: Estimated output tokens
            
        Returns:
            True if within budget
        """
        total_needed = input_tokens + output_tokens
        return total_needed <= self.max_tokens - 1000  # Leave 1000 token buffer
    
    def get_usage_percentage(self) -> float:
        """Get current token usage percentage"""
        if self.max_tokens == 0:
            return 0.0
        return (self.total_tokens / self.max_tokens) * 100
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, 
                      model: str = "gpt-4o-mini") -> float:
        """
        Estimate cost for token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        # Pricing per 1K tokens (approx)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        }
        
        rates = pricing.get(model, pricing["gpt-4o-mini"])
        
        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]
        
        return input_cost + output_cost
    
    def truncate_to_limit(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Input text
            max_tokens: Maximum tokens allowed
            
        Returns:
            Truncated text
        """
        if self.count_text(text) <= max_tokens:
            return text
        
        # Approximate truncation by characters
        max_chars = int(max_tokens * 4)
        
        if len(text) <= max_chars:
            return text
        
        # Truncate and add ellipsis
        truncated = text[:max_chars - 3] + "..."
        
        return truncated
    
    def get_optimization_suggestions(self, messages: List[Dict[str, str]]) -> List[str]:
        """
        Get suggestions for reducing token usage.
        
        Args:
            messages: List of messages
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        total_tokens = self.count_messages(messages)
        
        if total_tokens > self.max_tokens * 0.8:
            suggestions.append(f"Token usage is high ({total_tokens}/{self.max_tokens})")
            
            # Check for long user messages
            for i, msg in enumerate(messages):
                if msg.get("role") == "user":
                    tokens = self.count_text(msg.get("content", ""))
                    if tokens > 2000:
                        suggestions.append(f"User message {i+1} is very long ({tokens} tokens)")
            
            # Check for many messages
            if len(messages) > 20:
                suggestions.append(f"Conversation has {len(messages)} messages, consider summarizing")
            
            # Suggest summarization
            suggestions.append("Consider summarizing old conversation turns")
        
        return suggestions
    
    def format_token_report(self) -> str:
        """Generate a formatted token usage report"""
        report = f"""
        ========================================
        TOKEN USAGE REPORT
        ========================================
        Model: {self.model_name}
        Max Tokens: {self.max_tokens:,}
        
        Usage:
          Total Tokens: {self.total_tokens:,}
          Input Tokens: {self.input_tokens:,}
          Output Tokens: {self.output_tokens:,}
          API Calls: {self.call_count}
        
        Usage Percentage: {self.get_usage_percentage():.1f}%
        ========================================
        """
        return report.strip()


# Simple token counter for quick use
def quick_count(text: str) -> int:
    """Quick token count for a string"""
    counter = TokenCounter()
    return counter.count_text(text)


if __name__ == "__main__":
    # Test token counter
    print("=" * 50)
    print("TOKEN COUNTER TEST")
    print("=" * 50)
    
    counter = TokenCounter(model_name="gpt-4o-mini")
    
    # Test text
    test_text = "What is my checking account balance?"
    tokens = counter.count_text(test_text)
    print(f"\nText: '{test_text}'")
    print(f"Tokens: {tokens}")
    
    # Test messages
    messages = [
        {"role": "system", "content": "You are a helpful finance assistant."},
        {"role": "user", "content": "Transfer $500 to savings"},
        {"role": "assistant", "content": "I'll help you transfer $500 to savings."}
    ]
    
    msg_tokens = counter.count_messages(messages)
    print(f"\nMessages token count: {msg_tokens}")
    
    # Test budget check
    within_budget = counter.check_budget(msg_tokens, output_tokens=500)
    print(f"Within budget: {within_budget}")
    
    # Test cost estimate
    cost = counter.estimate_cost(msg_tokens, 500)
    print(f"Estimated cost: ${cost:.6f}")
    
    # Test optimization suggestions
    suggestions = counter.get_optimization_suggestions(messages)
    if suggestions:
        print(f"\nOptimization suggestions:")
        for s in suggestions:
            print(f"  • {s}")