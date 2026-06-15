# utils/compliance_logger.py
"""Compliance logging for audit trails and regulatory reporting"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from enum import Enum
import hashlib


class ComplianceEventType(str, Enum):
    """Compliance event types"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    TRANSACTION_INITIATED = "transaction_initiated"
    TRANSACTION_COMPLETED = "transaction_completed"
    TRANSACTION_FAILED = "transaction_failed"
    TRANSACTION_BLOCKED = "transaction_blocked"
    RISK_ALERT = "risk_alert"
    HUMAN_REVIEW_REQUESTED = "human_review_requested"
    HUMAN_REVIEW_COMPLETED = "human_review_completed"
    ACCOUNT_CHANGE = "account_change"
    AML_CHECK = "aml_check"
    FRAUD_CHECK = "fraud_check"
    REGULATORY_REPORT = "regulatory_report"
    DATA_ACCESS = "data_access"
    AUDIT_LOG_EXPORT = "audit_log_export"


class ComplianceLogger:
    """
    Compliance logging for audit trails.
    Immutable log entries with tamper detection.
    """
    
    def __init__(self, log_dir: str = "logs/compliance", 
                 enable_hashing: bool = True,
                 retention_days: int = 2555):  # 7 years typical
        """
        Initialize compliance logger.
        
        Args:
            log_dir: Directory for compliance logs
            enable_hashing: Enable hash chaining for tamper detection
            retention_days: Log retention in days
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.enable_hashing = enable_hashing
        self.retention_days = retention_days
        self.current_log_file = None
        self.last_hash = None
        self._init_log_file()
    
    def _init_log_file(self):
        """Initialize log file for current month"""
        current_month = datetime.now().strftime("%Y-%m")
        self.current_log_file = self.log_dir / f"compliance_{current_month}.jsonl"
        
        # Load last hash if file exists
        if self.enable_hashing and self.current_log_file.exists():
            try:
                with open(self.current_log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_entry = json.loads(lines[-1])
                        self.last_hash = last_entry.get("hash")
            except:
                self.last_hash = None
    
    def log_event(self, event_type: ComplianceEventType, 
                  user_id: str,
                  details: Dict[str, Any],
                  ip_address: Optional[str] = None,
                  session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Log a compliance event.
        
        Args:
            event_type: Type of compliance event
            user_id: User identifier
            details: Event details
            ip_address: Client IP address
            session_id: Session identifier
            
        Returns:
            Log entry dictionary
        """
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "event_id": self._generate_event_id(),
            "timestamp": timestamp,
            "event_type": event_type.value if hasattr(event_type, 'value') else str(event_type),
            "user_id": user_id,
            "details": details,
            "ip_address": ip_address,
            "session_id": session_id,
            "environment": os.getenv("APP_ENV", "development")
        }
        
        # Add hash for tamper detection
        if self.enable_hashing:
            log_entry["previous_hash"] = self.last_hash
            log_entry["hash"] = self._compute_hash(log_entry)
            self.last_hash = log_entry["hash"]
        
        # Write to log file
        with open(self.current_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Also write to separate event file for quick access
        self._write_event_file(event_type, log_entry)
        
        return log_entry
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"EVT_{timestamp}_{os.urandom(4).hex()}"
    
    def _compute_hash(self, entry: Dict[str, Any]) -> str:
        """Compute hash for tamper detection"""
        # Create copy without hash fields
        hash_data = {k: v for k, v in entry.items() 
                     if k not in ['hash', 'previous_hash']}
        
        # Sort keys for consistent hashing
        hash_string = json.dumps(hash_data, sort_keys=True)
        
        return hashlib.sha256(hash_string.encode()).hexdigest()[:16]
    
    def _write_event_file(self, event_type: ComplianceEventType, entry: Dict[str, Any]):
        """Write to event-specific file for easy querying"""
        event_dir = self.log_dir / "by_event"
        event_dir.mkdir(exist_ok=True)
        
        event_name = event_type.value if hasattr(event_type, 'value') else str(event_type)
        event_file = event_dir / f"{event_name}_{datetime.now().strftime('%Y%m')}.jsonl"
        
        with open(event_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def log_transaction(self, user_id: str, transaction: Dict[str, Any], 
                        status: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Log transaction for audit"""
        return self.log_event(
            event_type=ComplianceEventType.TRANSACTION_INITIATED,
            user_id=user_id,
            details={
                "transaction_id": transaction.get("transaction_id"),
                "amount": transaction.get("amount"),
                "currency": transaction.get("currency", "USD"),
                "recipient": transaction.get("recipient"),
                "status": status,
                "risk_score": transaction.get("risk_score"),
                "full_transaction": transaction
            },
            ip_address=ip_address,
            session_id=transaction.get("session_id")
        )
    
    def log_risk_alert(self, user_id: str, risk_score: int, 
                       risk_factors: List[str], ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Log risk alert"""
        return self.log_event(
            event_type=ComplianceEventType.RISK_ALERT,
            user_id=user_id,
            details={
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "alert_level": "high" if risk_score >= 70 else "medium" if risk_score >= 40 else "low"
            },
            ip_address=ip_address
        )
    
    def log_human_review(self, user_id: str, review_id: str, 
                         decision: str, reviewer_id: str,
                         ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Log human review decision"""
        return self.log_event(
            event_type=ComplianceEventType.HUMAN_REVIEW_COMPLETED,
            user_id=user_id,
            details={
                "review_id": review_id,
                "decision": decision,
                "reviewer_id": reviewer_id,
                "timestamp_reviewed": datetime.now().isoformat()
            },
            ip_address=ip_address
        )
    
    def query_logs(self, event_type: Optional[ComplianceEventType] = None,
                   user_id: Optional[str] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Query compliance logs.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum results
            
        Returns:
            List of log entries
        """
        results = []
        
        # Determine which files to scan
        files_to_scan = []
        if start_date and end_date:
            # Scan relevant months
            current = start_date.replace(day=1)
            while current <= end_date:
                month_file = self.log_dir / f"compliance_{current.strftime('%Y-%m')}.jsonl"
                if month_file.exists():
                    files_to_scan.append(month_file)
                current = self._add_months(current, 1)
        else:
            # Scan all files
            files_to_scan = list(self.log_dir.glob("compliance_*.jsonl"))
        
        # Scan files
        for log_file in files_to_scan:
            if len(results) >= limit:
                break
                
            with open(log_file, 'r') as f:
                for line in f:
                    if len(results) >= limit:
                        break
                    
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        if event_type and entry.get("event_type") != event_type.value:
                            continue
                        if user_id and entry.get("user_id") != user_id:
                            continue
                        if start_date:
                            entry_date = datetime.fromisoformat(entry["timestamp"])
                            if entry_date < start_date:
                                continue
                        if end_date:
                            entry_date = datetime.fromisoformat(entry["timestamp"])
                            if entry_date > end_date:
                                continue
                        
                        results.append(entry)
                        
                    except json.JSONDecodeError:
                        continue
        
        return results
    
    def _add_months(self, date: datetime, months: int) -> datetime:
        """Add months to date"""
        year = date.year + (date.month + months - 1) // 12
        month = (date.month + months - 1) % 12 + 1
        return datetime(year, month, 1)
    
    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify log integrity using hash chain.
        
        Returns:
            Verification results
        """
        results = {
            "verified": True,
            "errors": [],
            "entries_checked": 0,
            "chain_broken": False
        }
        
        previous_hash = None
        
        if not self.current_log_file.exists():
            return results
        
        with open(self.current_log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())
                    results["entries_checked"] += 1
                    
                    # Verify current hash
                    if "hash" in entry:
                        computed_hash = self._compute_hash(
                            {k: v for k, v in entry.items() 
                             if k not in ['hash', 'previous_hash']}
                        )
                        
                        if computed_hash != entry["hash"]:
                            results["verified"] = False
                            results["errors"].append(f"Line {line_num}: Hash mismatch")
                    
                    # Verify chain
                    if previous_hash is not None and "previous_hash" in entry:
                        if entry["previous_hash"] != previous_hash:
                            results["verified"] = False
                            results["chain_broken"] = True
                            results["errors"].append(f"Line {line_num}: Chain broken")
                    
                    previous_hash = entry.get("hash")
                    
                except json.JSONDecodeError as e:
                    results["verified"] = False
                    results["errors"].append(f"Line {line_num}: JSON decode error: {e}")
        
        return results
    
    def generate_compliance_report(self, start_date: datetime, 
                                    end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report for date range"""
        logs = self.query_logs(start_date=start_date, end_date=end_date, limit=10000)
        
        # Group by event type
        events_by_type = {}
        events_by_user = {}
        
        for log in logs:
            event_type = log.get("event_type")
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
            
            user_id = log.get("user_id")
            events_by_user[user_id] = events_by_user.get(user_id, 0) + 1
        
        report = {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.now().isoformat(),
            "total_events": len(logs),
            "events_by_type": events_by_type,
            "unique_users": len(events_by_user),
            "high_risk_events": len([l for l in logs 
                                     if l.get("details", {}).get("risk_score", 0) >= 70]),
            "human_review_events": len([l for l in logs 
                                        if "human_review" in l.get("event_type", "")])
        }
        
        return report


# Global compliance logger instance
_compliance_logger = None


def get_compliance_logger() -> ComplianceLogger:
    """Get or create compliance logger singleton"""
    global _compliance_logger
    if _compliance_logger is None:
        _compliance_logger = ComplianceLogger()
    return _compliance_logger


if __name__ == "__main__":
    print("=" * 50)
    print("COMPLIANCE LOGGER TEST")
    print("=" * 50)
    
    logger = get_compliance_logger()
    
    # Log some events
    print("\nLogging events...")
    
    logger.log_event(
        ComplianceEventType.USER_LOGIN,
        user_id="user_123",
        details={"login_method": "password", "success": True},
        ip_address="192.168.1.100"
    )
    
    logger.log_transaction(
        user_id="user_123",
        transaction={"amount": 1000.00, "recipient": "SAVINGS_001"},
        status="completed"
    )
    
    logger.log_risk_alert(
        user_id="user_123",
        risk_score=85,
        risk_factors=["large_amount", "crypto_recipient"]
    )
    
    # Query logs
    print("\nQuerying logs...")
    logs = logger.query_logs(limit=10)
    print(f"  Found {len(logs)} log entries")
    
    for log in logs[:3]:
        print(f"  - {log['event_type']}: {log['user_id']} - {log['timestamp']}")
    
    # Verify integrity
    print("\nVerifying integrity...")
    verification = logger.verify_integrity()
    print(f"  Verified: {verification['verified']}")
    print(f"  Entries checked: {verification['entries_checked']}")
    
    if verification['errors']:
        print(f"  Errors: {verification['errors']}")
    
    # Generate report
    print("\nGenerating compliance report...")
    from datetime import timedelta
    report = logger.generate_compliance_report(
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )
    print(f"  Total events: {report['total_events']}")
    print(f"  Unique users: {report['unique_users']}")
    print(f"  Events by type: {report['events_by_type']}")