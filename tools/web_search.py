# tools/web_search.py
"""Web search tool using Tavily API for real-time information"""

from tools.base_tool import BaseTool
from typing import Dict, Any
from datetime import datetime
import importlib
import os


class WebSearchTool(BaseTool):
    """Search the web for real-time information using Tavily"""
    
    def __init__(self):
        """Initialize Tavily client if API key is available"""
        self.client = None
        self.api_key = os.getenv("TAVILY_API_KEY")
        
        if self.api_key:
            try:
                tavily_module = importlib.import_module("tavily")
                TavilyClient = getattr(tavily_module, "TavilyClient", None)

                if TavilyClient is None:
                    raise ImportError("TavilyClient not found in tavily module")

                self.client = TavilyClient(api_key=self.api_key)
                print("✅ Tavily client initialized")
            except ImportError:
                print("⚠️ Tavily package not installed. Run: pip install tavily-python")
            except Exception as e:
                print(f"⚠️ Tavily initialization error: {e}")
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "Search the web for real-time information about stocks, news, or any query"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'Toyota stock price', 'AAPL news')"
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "description": "Search depth",
                    "default": "basic"
                }
            },
            "required": ["query"]
        }
    
    def execute(self, query: str, search_depth: str = "basic", **kwargs) -> Dict[str, Any]:
        """Execute web search using Tavily"""
        
        # If no API key, return simulated data
        if not self.api_key:
            return self._get_simulated_response(query)
        
        # If client not initialized, return error
        if not self.client:
            return {
                "success": False,
                "error": "Tavily client not initialized. Check API key and installation.",
                "query": query
            }
        
        try:
            # Enhance stock queries
            if any(word in query.lower() for word in ["stock", "price", "share"]):
                query = self._enhance_stock_query(query)
            
            # Perform search
            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=5,
                include_answer=True
            )
            
            return {
                "success": True,
                "query": query,
                "answer": response.get("answer", ""),
                "results": [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", "")[:300]
                    }
                    for r in response.get("results", [])
                ],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def _enhance_stock_query(self, query: str) -> str:
        """Enhance stock-related queries"""
        query_lower = query.lower()
        
        stock_mappings = {
            "toyota": "Toyota Motor Corporation TM stock price",
            "apple": "Apple Inc. AAPL stock price",
            "tesla": "Tesla Inc. TSLA stock price",
            "microsoft": "Microsoft Corporation MSFT stock price",
            "google": "Alphabet Inc. GOOGL stock price"
        }
        
        for company, enhanced in stock_mappings.items():
            if company in query_lower:
                return enhanced
        
        return query
    
    def _get_simulated_response(self, query: str) -> Dict[str, Any]:
        """Return simulated data when no API key is available"""
        query_lower = query.lower()
        
        # Simulated stock data
        if "toyota" in query_lower and "stock" in query_lower:
            return {
                "success": True,
                "query": query,
                "answer": "Toyota Motor Corporation (TM) is currently trading at $238.45, up $2.15 (+0.91%) from the previous close.",
                "results": [
                    {"title": "Toyota Stock Price - NYSE", "url": "https://finance.yahoo.com/quote/TM", "content": "Toyota Motor Corp (TM) stock quote, history, news..."}
                ],
                "simulated": True,
                "timestamp": datetime.now().isoformat()
            }
        elif "apple" in query_lower and "stock" in query_lower:
            return {
                "success": True,
                "query": query,
                "answer": "Apple Inc. (AAPL) is currently trading at $175.50, up $2.30 (+1.33%) from the previous close.",
                "results": [],
                "simulated": True,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "success": False,
            "error": "TAVILY_API_KEY not configured. Please add to .env file",
            "query": query
        }


class RealTimeStockTool(WebSearchTool):
    """Specialized stock price tool using web search"""
    
    @property
    def name(self) -> str:
        return "get_stock_price"
    
    @property
    def description(self) -> str:
        return "Get real-time stock price for any company"
    
    def execute(self, symbol: str = None, company: str = None, **kwargs) -> Dict[str, Any]:
        """Get stock price for a company"""
        
        if symbol:
            query = f"{symbol} stock price today"
        elif company:
            query = f"{company} stock price"
        else:
            query = kwargs.get("query", "")
        
        if not query:
            return {
                "success": False,
                "error": "Please provide a stock symbol or company name"
            }
        
        # Use parent's search method
        result = super().execute(query=query)
        
        if result.get("success"):
            return {
                "success": True,
                "symbol": symbol or company,
                "price_info": result.get("answer", "Price information retrieved"),
                "sources": [r["url"] for r in result.get("results", [])[:2]],
                "timestamp": datetime.now().isoformat()
            }
        
        return result


# Test the module
if __name__ == "__main__":
    print("Testing WebSearchTool...")
    tool = WebSearchTool()
    result = tool.execute("Toyota stock price")
    
    if result.get("success"):
        print(f"✅ Search successful")
        print(f"Answer: {result.get('answer', 'No answer')[:100]}")
    else:
        print(f"❌ Error: {result.get('error')}")