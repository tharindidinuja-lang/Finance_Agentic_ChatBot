# risk_checks/regulatory_checker.py
"""Regulatory compliance checker (Reg D, limits, etc.)"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class RegulationType(Enum):
    REG_D = "Regulation D"  # Savings account withdrawal limits
    REG_E = "Regulation E"  # Electronic fund transfers
    REG_CC = "Regulation CC"  # Funds availability
    BSA = "Bank Secrecy Act"  # Reporting requirements
    OFAC = "OFAC Sanctions"  # Sanctions compliance


@dataclass
class RegulationViolation:
    """Regulation violation record"""
    regulation: RegulationType
    rule_name: str
    description: str
    severity: str  # low, medium, high, critical
    limit: float
    actual_value: float
    recommendation: str


class RegulatoryChecker:
    """
    Regulatory compliance checker for banking regulations.
    Enforces Reg D, transfer limits, and reporting requirements.
    """
    
    def __init__(self):
        # Regulation D limits (savings account withdrawals)
        self.reg_d_withdrawal_limit = 6  # 6 per month
        self.reg_d_excess_fee = 10.00  # $10 fee for excess
        
        # Reg CC funds availability schedule
        self.funds_availability = {
            "local_check": 2,  # 2 business days
            "nonlocal_check": 5,  # 5 business days
            "wire_transfer": 0,  # Same day
            "ach": 1,  # Next business day
        }
        
        # BSA reporting thresholds
        self.ctr_threshold = 10000.00  # Currency Transaction Report
        self.sar_threshold = 5000.00  # Suspicious Activity Report
        
        # Daily and monthly limits (user-specific, set defaults)
        self.default_daily_limit = 10000.00
        self.default_monthly_limit = 50000.00
    
    def check_transaction(self, transaction: Dict[str, Any], 
                          user_profile: Dict[str, Any],
                          user_history: List[Dict]) -> Tuple[bool, List[RegulationViolation]]:
        """
        Check transaction for regulatory compliance.
        
        Returns:
            Tuple of (is_compliant, list_of_violations)
        """
        violations = []
        is_compliant = True
        
        # Check 1: Reg D - Savings withdrawal limits
        reg_d_violations = self._check_reg_d(transaction, user_history)
        if reg_d_violations:
            violations.extend(reg_d_violations)
            is_compliant = False
        
        # Check 2: Daily transfer limits
        daily_violations = self._check_daily_limit(transaction, user_history, user_profile)
        if daily_violations:
            violations.extend(daily_violations)
            is_compliant = False
        
        # Check 3: Monthly transfer limits
        monthly_violations = self._check_monthly_limit(transaction, user_history, user_profile)
        if monthly_violations:
            violations.extend(monthly_violations)
            is_compliant = False
        
        # Check 4: BSA reporting requirements
        bsa_violations = self._check_bsa_reporting(transaction, user_history)
        if bsa_violations:
            violations.extend(bsa_violations)
            # BSA violations require reporting but don't block necessarily
        
        # Check 5: Reg E - Electronic transfer rights
        reg_e_violations = self._check_reg_e(transaction, user_profile)
        if reg_e_violations:
            violations.extend(reg_e_violations)
        
        return is_compliant, violations
    
    def _check_reg_d(self, transaction: Dict, history: List[Dict]) -> List[RegulationViolation]:
        """Check Regulation D (savings withdrawal limits)"""
        violations = []
        
        # Only applies to savings accounts
        if transaction.get("account_type") != "savings":
            return violations
        
        if transaction.get("type") not in ["withdrawal", "transfer"]:
            return violations
        
        # Count withdrawals in current month
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        
        savings_withdrawals = [
            tx for tx in history
            if tx.get("account_type") == "savings"
            and tx.get("type") in ["withdrawal", "transfer"]
            and tx.get("timestamp", now) >= month_start
        ]
        
        withdrawal_count = len(savings_withdrawals) + 1  # +1 for current transaction
        
        if withdrawal_count > self.reg_d_withdrawal_limit:
            violations.append(RegulationViolation(
                regulation=RegulationType.REG_D,
                rule_name="savings_withdrawal_limit",
                description=f"Exceeds monthly savings withdrawal limit of {self.reg_d_withdrawal_limit}",
                severity="medium",
                limit=self.reg_d_withdrawal_limit,
                actual_value=withdrawal_count,
                recommendation=f"Excess fee of ${self.reg_d_excess_fee:.2f} will apply"
            ))
        
        return violations
    
    def _check_daily_limit(self, transaction: Dict, history: List[Dict], 
                          user_profile: Dict) -> List[RegulationViolation]:
        """Check daily transfer limits"""
        violations = []
        
        amount = transaction.get("amount", 0)
        daily_limit = user_profile.get("daily_transfer_limit", self.default_daily_limit)
        
        # Calculate today's total outflows
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_outflows = sum(
            tx.get("amount", 0)
            for tx in history
            if tx.get("type") in ["transfer", "debit", "withdrawal"]
            and tx.get("timestamp", datetime.now()) >= today
        )
        
        total_today = today_outflows + amount
        
        if total_today > daily_limit:
            violations.append(RegulationViolation(
                regulation=RegulationType.REG_E,
                rule_name="daily_transfer_limit",
                description=f"Exceeds daily transfer limit of ${daily_limit:,.2f}",
                severity="high",
                limit=daily_limit,
                actual_value=total_today,
                recommendation=f"Transaction would exceed limit by ${total_today - daily_limit:,.2f}"
            ))
        
        return violations
    
    def _check_monthly_limit(self, transaction: Dict, history: List[Dict],
                            user_profile: Dict) -> List[RegulationViolation]:
        """Check monthly transfer limits"""
        violations = []
        
        amount = transaction.get("amount", 0)
        monthly_limit = user_profile.get("monthly_transfer_limit", self.default_monthly_limit)
        
        # Calculate month-to-date outflows
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        month_outflows = sum(
            tx.get("amount", 0)
            for tx in history
            if tx.get("type") in ["transfer", "debit", "withdrawal"]
            and tx.get("timestamp", datetime.now()) >= month_start
        )
        
        total_month = month_outflows + amount
        
        if total_month > monthly_limit:
            violations.append(RegulationViolation(
                regulation=RegulationType.REG_E,
                rule_name="monthly_transfer_limit",
                description=f"Exceeds monthly transfer limit of ${monthly_limit:,.2f}",
                severity="high",
                limit=monthly_limit,
                actual_value=total_month,
                recommendation=f"Transaction would exceed limit by ${total_month - monthly_limit:,.2f}"
            ))
        
        return violations
    
    def _check_bsa_reporting(self, transaction: Dict, history: List[Dict]) -> List[RegulationViolation]:
        """Check BSA reporting requirements"""
        violations = []
        
        amount = transaction.get("amount", 0)
        
        # CTR reporting ($10,000+ cash transactions)
        if amount >= self.ctr_threshold and transaction.get("type") == "cash_deposit":
            violations.append(RegulationViolation(
                regulation=RegulationType.BSA,
                rule_name="ctr_required",
                description=f"Currency Transaction Report required for ${amount:,.2f} cash transaction",
                severity="medium",
                limit=self.ctr_threshold,
                actual_value=amount,
                recommendation="File FinCEN Form 112 within 15 days"
            ))
        
        # Check for structured transactions (multiple just under threshold)
        if self._detect_structuring(history):
            violations.append(RegulationViolation(
                regulation=RegulationType.BSA,
                rule_name="structuring_detected",
                description="Potential transaction structuring (smurfing) detected",
                severity="high",
                limit=self.ctr_threshold,
                actual_value=self._calculate_structuring_total(history),
                recommendation="File Suspicious Activity Report (SAR)"
            ))
        
        return violations
    
    