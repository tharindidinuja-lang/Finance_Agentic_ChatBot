# tools/base_tool.py
from pydantic import BaseModel, Field
from typing import Any, Dict, Callable
from abc import ABC, abstractmethod

class BaseTool(ABC):
    """Base class for all finance tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Pydantic schema for LLM tool calling"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema()
            }
        }
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        pass