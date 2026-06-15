# memory/conversation_buffer.py
"""Short-term conversation memory with sliding window and summarization"""

from typing import List, Dict, Any, Optional
from collections import deque
from datetime import datetime
import json
import os


class ConversationBuffer:
    """
    Manages short-term conversation history with sliding window.
    Can summarize old messages to save tokens.
    """
    
    def __init__(self, max_messages: int = 50, enable_summarization: bool = True):
        """
        Initialize conversation buffer.
        
        Args:
            max_messages: Maximum number of messages to keep (oldest are dropped)
            enable_summarization: Whether to summarize old messages instead of dropping
        """
        self.max_messages = max_messages
        self.enable_summarization = enable_summarization
        self.messages: deque = deque(maxlen=max_messages)
        self.summary: Optional[str] = None
        self.message_count = 0
        self.last_updated = datetime.now()
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a message to the buffer.
        
        Args:
            role: 'user', 'assistant', or 'system'
            content: Message content
            metadata: Optional metadata (timestamp, intent, etc.)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        self.message_count += 1
        self.last_updated = datetime.now()
        
        # Trigger summarization if buffer is getting full
        if self.enable_summarization and len(self.messages) >= self.max_messages * 0.8:
            self._maybe_summarize()
    
    def get_messages(self, last_n: Optional[int] = None) -> List[Dict]:
        """
        Get messages from buffer.
        
        Args:
            last_n: Number of recent messages to return (None for all)
            
        Returns:
            List of message dictionaries
        """
        if last_n is None:
            return list(self.messages)
        else:
            return list(self.messages)[-last_n:]
    
    def get_formatted_for_llm(self, include_summary: bool = True) -> str:
        """
        Format messages for LLM context.
        
        Args:
            include_summary: Whether to include conversation summary
            
        Returns:
            Formatted string for LLM
        """
        formatted = []
        
        # Add summary if available
        if include_summary and self.summary:
            formatted.append(f"[Conversation Summary]: {self.summary}\n")
        
        # Add recent messages
        for msg in self.messages:
            role = msg["role"].upper()
            content = msg["content"]
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def get_context_window(self, token_limit: int = 4000) -> List[Dict]:
        """
        Get messages within token limit (approximate).
        
        Args:
            token_limit: Approximate token limit (1 token ~ 4 chars for English)
            
        Returns:
            List of messages that fit within token limit
        """
        messages = list(self.messages)
        result = []
        total_chars = 0
        
        # Start from most recent
        for msg in reversed(messages):
            msg_chars = len(msg["content"]) + 20  # +20 for role and formatting
            if total_chars + msg_chars <= token_limit * 4:
                result.insert(0, msg)
                total_chars += msg_chars
            else:
                break
        
        return result
    
    def _maybe_summarize(self):
        """Generate summary of older messages if buffer is large."""
        # This would typically call an LLM to summarize
        # For now, we'll create a simple summary
        if len(self.messages) > self.max_messages // 2:
            old_messages = list(self.messages)[:len(self.messages)//2]
            summary_text = self._create_simple_summary(old_messages)
            self.summary = summary_text
    
    def _create_simple_summary(self, messages: List[Dict]) -> str:
        """Create a simple summary of messages."""
        topics = set()
        for msg in messages:
            content_lower = msg["content"].lower()
            if "balance" in content_lower or "money" in content_lower:
                topics.add("financial inquiries")
            elif "transfer" in content_lower or "send" in content_lower:
                topics.add("transfers")
            elif "stock" in content_lower or "price" in content_lower:
                topics.add("market data")
        
        if topics:
            return f"User discussed {', '.join(topics)}. "
        return "General conversation. "
    
    def clear(self):
        """Clear all messages from buffer."""
        self.messages.clear()
        self.summary = None
        self.last_updated = datetime.now()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        return {
            "total_messages": len(self.messages),
            "total_conversation_messages": self.message_count,
            "has_summary": self.summary is not None,
            "last_updated": self.last_updated.isoformat(),
            "buffer_full": len(self.messages) == self.max_messages
        }
    
    def save_to_file(self, filepath: str):
        """Save buffer to file for persistence."""
        data = {
            "messages": list(self.messages),
            "summary": self.summary,
            "message_count": self.message_count,
            "last_updated": self.last_updated.isoformat()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filepath: str):
        """Load buffer from file."""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.messages = deque(data["messages"], maxlen=self.max_messages)
            self.summary = data.get("summary")
            self.message_count = data.get("message_count", 0)
            self.last_updated = datetime.fromisoformat(data["last_updated"])


# Test the conversation buffer
if __name__ == "__main__":
    print("="*60)
    print("Conversation Buffer Test")
    print("="*60)
    
    # Create buffer
    buffer = ConversationBuffer(max_messages=10)
    
    # Add some messages
    buffer.add_message("user", "What's my checking account balance?")
    buffer.add_message("assistant", "Your checking balance is $5,420.50")
    buffer.add_message("user", "Transfer $500 to savings")
    buffer.add_message("assistant", "Transfer completed successfully")
    
    # Get formatted for LLM
    print("\nFormatted for LLM:")
    print(buffer.get_formatted_for_llm())
    
    # Get stats
    print("\nBuffer Stats:")
    for key, value in buffer.get_stats().items():
        print(f"  {key}: {value}")
    
    # Test context window
    print("\nContext Window (1000 chars limit):")
    context = buffer.get_context_window(token_limit=250)  # ~1000 chars
    for msg in context:
        print(f"  {msg['role']}: {msg['content'][:50]}...")