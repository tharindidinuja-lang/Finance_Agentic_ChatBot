# tools/loan_calculator.py
"""Calculate loan EMIs, eligibility, and amortization"""

from tools.base_tool import BaseTool
from typing import Dict, Any, List
from math import pow


class LoanCalculatorTool(BaseTool):
    """Calculate loan payments, EMI, and amortization schedule"""
    
    @property
    def name(self) -> str:
        return "calculate_loan"
    
    @property
    def description(self) -> str:
        return "Calculate loan EMI, total interest, and amortization schedule"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "principal": {
                    "type": "number",
                    "description": "Loan amount"
                },
                "annual_rate": {
                    "type": "number",
                    "description": "Annual interest rate (percentage)"
                },
                "years": {
                    "type": "integer",
                    "description": "Loan term in years"
                },
                "down_payment": {
                    "type": "number",
                    "description": "Down payment amount",
                    "default": 0
                },
                "calculate_amortization": {
                    "type": "boolean",
                    "description": "Generate amortization schedule",
                    "default": False
                }
            },
            "required": ["principal", "annual_rate", "years"]
        }
    
    def execute(self, principal: float, annual_rate: float, years: int, 
                down_payment: float = 0, calculate_amortization: bool = False, **kwargs) -> Dict[str, Any]:
        """Calculate loan details"""
        
        # Adjust principal for down payment
        loan_amount = principal - down_payment
        
        if loan_amount <= 0:
            return {
                "success": False,
                "error": "Loan amount must be positive after down payment"
            }
        
        # Monthly calculations
        monthly_rate = annual_rate / 100 / 12
        months = years * 12
        
        # Calculate EMI (Equated Monthly Installment)
        if monthly_rate > 0:
            emi = loan_amount * monthly_rate * pow(1 + monthly_rate, months) / (pow(1 + monthly_rate, months) - 1)
        else:
            emi = loan_amount / months
        
        # Calculate totals
        total_payment = emi * months
        total_interest = total_payment - loan_amount
        
        result = {
            "success": True,
            "loan_amount": round(loan_amount, 2),
            "principal": round(principal, 2),
            "down_payment": round(down_payment, 2),
            "annual_rate": annual_rate,
            "years": years,
            "emi": round(emi, 2),
            "total_interest": round(total_interest, 2),
            "total_payment": round(total_payment, 2),
            "interest_percentage": round((total_interest / loan_amount) * 100, 2)
        }
        
        # Calculate amortization schedule if requested
        if calculate_amortization:
            result["amortization"] = self._calculate_amortization(loan_amount, monthly_rate, months, emi)
        
        return result
    
    def _calculate_amortization(self, principal: float, monthly_rate: float, 
                                months: int, emi: float) -> List[Dict]:
        """Calculate detailed amortization schedule"""
        
        schedule = []
        balance = principal
        
        for month in range(1, months + 1):
            interest = balance * monthly_rate
            principal_paid = emi - interest
            balance -= principal_paid
            
            schedule.append({
                "month": month,
                "payment": round(emi, 2),
                "principal": round(principal_paid, 2),
                "interest": round(interest, 2),
                "balance": round(max(0, balance), 2)
            })
            
            if balance <= 0:
                break
        
        return schedule
    
    def check_eligibility(self, monthly_income: float, existing_emis: float = 0) -> Dict:
        """Check loan eligibility based on income"""
        max_emi = monthly_income * 0.4  # 40% of income
        available_for_new = max_emi - existing_emis
        
        return {
            "max_emi_allowed": round(max_emi, 2),
            "available_for_new_loan": round(available_for_new, 2),
            "is_eligible": available_for_new > 0
        }


# Test
if __name__ == "__main__":
    tool = LoanCalculatorTool()
    
    # Calculate home loan
    result = tool.execute(
        principal=300000,  # $300,000
        annual_rate=6.5,   # 6.5% APR
        years=30,          # 30 years
        down_payment=60000  # $60,000 down
    )
    
    print(f"Loan Calculator Results:")
    print(f"  Loan Amount: ${result['loan_amount']:,.2f}")
    print(f"  Monthly EMI: ${result['emi']:,.2f}")
    print(f"  Total Interest: ${result['total_interest']:,.2f}")
    print(f"  Total Payment: ${result['total_payment']:,.2f}")
    
    # Check eligibility
    eligibility = tool.check_eligibility(monthly_income=8000, existing_emis=500)
    print(f"\nEligibility Check:")
    print(f"  Max EMI Allowed: ${eligibility['max_emi_allowed']:,.2f}")
    print(f"  Eligible: {eligibility['is_eligible']}")