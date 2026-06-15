"""Helpers for working with both plain dict messages and LangChain BaseMessage objects."""

from typing import Any, Dict, List


def get_message_role(message: Any) -> str:
    """Return the role/type for a message object in a consistent format."""
    if isinstance(message, dict):
        role = message.get("role") or message.get("type")
        return role or "unknown"

    msg_type = getattr(message, "type", None)
    if msg_type in {"human", "ai", "assistant", "system", "user"}:
        return {"human": "user", "ai": "assistant"}.get(msg_type, msg_type)

    return "unknown"


def get_message_content(message: Any) -> str:
    """Return the text content of a message object."""
    if isinstance(message, dict):
        return str(message.get("content", ""))

    return str(getattr(message, "content", ""))


def normalize_messages(messages: List[Any]) -> List[Dict[str, Any]]:
    """Convert a list of messages to plain dictionaries for safe downstream use."""
    return [
        {"role": get_message_role(message), "content": get_message_content(message)}
        for message in messages
    ]
