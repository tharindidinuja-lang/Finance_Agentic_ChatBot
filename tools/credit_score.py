# tools/credit_score.py
"""Get and analyze credit score"""

from tools.base_tool import BaseTool
from typing import Dict, Any, List
from datetime import datetime
import random


class CreditScoreTool(BaseTool):
    """Get user's credit score and report factors"""
    
    @property
    def name(self) -> str:
        return "get_credit_score"
    
    @property
    def description(self) -> str:
        return "Get credit score and factors affecting it"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier"
                },
                "include_factors": {
                    "type": "boolean",
                    "description": "Include credit factors",
                    "default": True
                }
            },
            "required": ["user_id"]
        }
    
    def execute(self, user_id: str, include_factors: bool = True, **kwargs) -> Dict[str, Any]:
        """Get credit score"""
        
        # Get simulated credit score
        credit_data = self._get_simulated_credit_score(user_id)
        
        result = {
            "success": True,
            "user_id": user_id,
            "credit_score": credit_data["score"],
            "rating": credit_data["rating"],
            "last_updated": datetime.now().isoformat(),
            "bureau": "Experian"  # Simulated
        }
        
        if include_factors:
            result["factors"] = credit_data["factors"]
        
        return result
    
    def _get_simulated_credit_score(self, user_id: str) -> Dict:
        """Generate simulated credit score data"""
        
        # Credit score ranges
        # 300-579: Poor, 580-669: Fair, 670-739: Good, 740-799: Very Good, 800-850: Excellent
        
        # Simulate different scores for different users
        user_scores = {
            "user_123": 720,
            "test_user_001": 680,
            "premium_user": 780,
            "new_user": 650,
        }
        
        score = user_scores.get(user_id, random.randint(600, 750))
        
        # Determine rating
        if score >= 800:
            rating = "Excellent"
        elif score >= 740:
            rating = "Very Good"
        elif score >= 670:
            rating = "Good"
        elif score >= 580:
            rating = "Fair"
        else:
            rating = "Poor"
        
        # Credit factors
        factors = [
            {
                "factor": "Payment History",
                "impact": "Positive" if score > 700 else "Moderate",
                "details": "No late payments in last 24 months"
            },
            {
                "factor": "Credit Utilization",
                "impact": "Positive" if score > 700 else "Needs Improvement",
                "details": f"Using {random.randint(10, 50)}% of available credit"
            },
            {
                "factor": "Credit Age",
                "impact": "Positive",
                "details": f"Average account age: {random.randint(3, 15)} years"
            },
            {
                "factor": "Recent Inquiries",
                "impact": "Low",
                "details": f"{random.randint(0, 3)} inquiries in last 12 months"
            }
        ]
        
        return {
            "score": score,
            "rating": rating,
            "factors": factors
        }


# Test
if __name__ == "__main__":
    tool = CreditScoreTool()
    result = tool.execute(user_id="user_123", include_factors=True)
    
    print(f"Credit Score: {result['credit_score']} ({result['rating']})")
    print(f"\nFactors Affecting Score:")
    for factor in result.get('factors', []):
        print(f"  • {factor['factor']}: {factor['impact']} - {factor['details']}")