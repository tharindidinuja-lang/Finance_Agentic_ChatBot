# workflows/__init__.py
"""
Workflows module for Finance Agentic Chatbot.

Contains LangGraph graph definitions and conditional routing logic
for the multi-agent conversation workflow.
"""

# ============================================================================
# Main Graph Imports
# ============================================================================

from workflows.finance_graph import (
    create_finance_graph,
    get_finance_app,
    reset_workflow_state,
    workflow_config,
    FinanceWorkflowConfig,
)

from workflows.conditional_routing import (
    # Main routing functions
    route_after_classifier,
    route_after_planner,
    route_after_tool_decision,
    route_after_tool_execution,
    route_after_validation,
    route_after_retry,
    route_after_risk_check,
    route_after_human_review,
    route_after_response,
    
    # Helper functions
    should_execute_more_tools,
    is_transaction_complete,
    needs_clarification,
    
    # Utilities
    get_next_node,
    print_routing_summary,
    CONDITIONAL_ROUTES,
)


# ============================================================================
# Workflow Constants
# ============================================================================

# Node names (for consistent referencing)
NODE_NAMES = {
    "CLASSIFIER": "classifier",
    "PLANNER": "planner",
    "TOOL_DECISION": "tool_decision",
    "TOOL_EXECUTION": "tool_execution",
    "VALIDATION": "validation",
    "RETRY": "retry",
    "RISK_CHECK": "risk_check",
    "HUMAN_REVIEW": "human_review",
    "RESPONSE_GENERATION": "response_generation",
}

# Edge types
EDGE_TYPES = {
    "STANDARD": "standard",
    "CONDITIONAL": "conditional",
    "FIXED": "fixed",
}

# Workflow stages
WORKFLOW_STAGES = {
    "INITIALIZING": "initializing",
    "CLASSIFYING": "classifying",
    "PLANNING": "planning",
    "EXECUTING": "executing",
    "VALIDATING": "validating",
    "RETRYING": "retrying",
    "ASSESSING_RISK": "assessing_risk",
    "HUMAN_REVIEW": "human_review",
    "RESPONDING": "responding",
    "COMPLETED": "completed",
    "FAILED": "failed",
}


# ============================================================================
# Workflow State Management
# ============================================================================

class WorkflowStateManager:
    """
    Helper class to manage workflow state and transitions.
    Useful for debugging and monitoring workflow execution.
    """
    
    def __init__(self):
        self.current_stage = None
        self.stage_history = []
        self.node_execution_times = {}
    
    def start_stage(self, stage: str):
        """Record start of a workflow stage"""
        import time
        self.current_stage = stage
        self.stage_history.append({
            "stage": stage,
            "start_time": time.time(),
            "status": "started"
        })
    
    def end_stage(self, stage: str):
        """Record end of a workflow stage"""
        import time
        for entry in reversed(self.stage_history):
            if entry["stage"] == stage and entry.get("status") == "started":
                entry["end_time"] = time.time()
                entry["duration"] = entry["end_time"] - entry["start_time"]
                entry["status"] = "completed"
                break
    
    def record_node_execution(self, node_name: str, duration_ms: float):
        """Record node execution time"""
        if node_name not in self.node_execution_times:
            self.node_execution_times[node_name] = []
        self.node_execution_times[node_name].append(duration_ms)
    
    def get_average_node_times(self) -> dict:
        """Get average execution time per node"""
        avg_times = {}
        for node, times in self.node_execution_times.items():
            if times:
                avg_times[node] = sum(times) / len(times)
        return avg_times
    
    def get_stage_summary(self) -> dict:
        """Get summary of workflow stages"""
        completed_stages = [s for s in self.stage_history if s.get("status") == "completed"]
        total_duration = sum(s.get("duration", 0) for s in completed_stages)
        
        return {
            "total_stages": len(self.stage_history),
            "completed_stages": len(completed_stages),
            "total_duration_seconds": round(total_duration, 3),
            "current_stage": self.current_stage,
            "stage_breakdown": [
                {
                    "stage": s["stage"],
                    "duration_ms": round(s.get("duration", 0) * 1000, 2)
                }
                for s in completed_stages
            ]
        }
    
    def reset(self):
        """Reset state manager"""
        self.current_stage = None
        self.stage_history = []
        self.node_execution_times = {}


# Global state manager instance
_workflow_state_manager = None

def get_workflow_state_manager() -> WorkflowStateManager:
    """Get or create workflow state manager singleton"""
    global _workflow_state_manager
    if _workflow_state_manager is None:
        _workflow_state_manager = WorkflowStateManager()
    return _workflow_state_manager


# ============================================================================
# Workflow Validation Functions
# ============================================================================

def validate_workflow():
    """
    Validate that the workflow is properly configured.
    Checks that all nodes and routes are defined.
    """
    print("\n🔍 Validating Workflow Configuration...")
    print("="*50)
    
    errors = []
    warnings = []
    
    # Check that all required nodes are in CONDITIONAL_ROUTES
    required_nodes = [
        "classifier", "planner", "tool_decision", "tool_execution",
        "validation", "retry", "risk_check", "human_review"
    ]
    
    for node in required_nodes:
        if node not in CONDITIONAL_ROUTES:
            errors.append(f"Missing routing for node: {node}")
        else:
            print(f"   ✅ {node} → {CONDITIONAL_ROUTES[node]['destinations']}")
    
    # Check for circular dependencies
    def has_circular_route(node, visited=None):
        if visited is None:
            visited = set()
        if node in visited:
            return True
        visited.add(node)
        if node in CONDITIONAL_ROUTES:
            for dest in CONDITIONAL_ROUTES[node]["destinations"]:
                if dest in CONDITIONAL_ROUTES and has_circular_route(dest, visited.copy()):
                    return True
        return False
    
    for node in CONDITIONAL_ROUTES:
        if has_circular_route(node):
            warnings.append(f"Potential circular route detected from {node}")
    
    # Print results
    if errors:
        print("\n ERRORS FOUND:")
        for error in errors:
            print(f"   • {error}")
    
    if warnings:
        print("\n  WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not errors and not warnings:
        print("\n Workflow validation passed!")
    
    print("="*50)
    
    return len(errors) == 0

# ============================================================================
# Workflow Metrics and Monitoring
# ============================================================================

class WorkflowMetrics:
    """Track workflow performance metrics"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.average_duration_ms = 0
        self.node_metrics = {}
    
    def record_execution(self, success: bool, duration_ms: float, node_metrics: dict = None):
        """Record a workflow execution"""
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
        
        # Update average duration
        self.average_duration_ms = (
            (self.average_duration_ms * (self.total_executions - 1) + duration_ms) 
            / self.total_executions
        )
        
        if node_metrics:
            for node, duration in node_metrics.items():
                if node not in self.node_metrics:
                    self.node_metrics[node] = []
                self.node_metrics[node].append(duration)
    
    def get_summary(self) -> dict:
        """Get metrics summary"""
        success_rate = (self.successful_executions / self.total_executions * 100) if self.total_executions > 0 else 0
        
        node_averages = {}
        for node, durations in self.node_metrics.items():
            if durations:
                node_averages[node] = {
                    "avg_ms": sum(durations) / len(durations),
                    "count": len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                }
        
        return {
            "total_executions": self.total_executions,
            "successful": self.successful_executions,
            "failed": self.failed_executions,
            "success_rate_percent": round(success_rate, 2),
            "average_duration_ms": round(self.average_duration_ms, 2),
            "node_performance": node_averages,
        }
    
    def print_summary(self):
        """Print metrics summary"""
        summary = self.get_summary()
        print("\n" + "="*50)
        print("WORKFLOW METRICS SUMMARY")
        print("="*50)
        print(f"Total Executions: {summary['total_executions']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate_percent']}%")
        print(f"Avg Duration: {summary['average_duration_ms']} ms")
        
        if summary['node_performance']:
            print("\nNode Performance:")
            for node, metrics in summary['node_performance'].items():
                print(f"  • {node}: avg {metrics['avg_ms']:.2f}ms (n={metrics['count']})")
        print("="*50)


# Global metrics instance
_workflow_metrics = None

def get_workflow_metrics() -> WorkflowMetrics:
    """Get or create workflow metrics singleton"""
    global _workflow_metrics
    if _workflow_metrics is None:
        _workflow_metrics = WorkflowMetrics()
    return _workflow_metrics


def visualize_workflow() -> str:
    """Return a simple text visualization of the workflow graph."""
    return "classifier -> planner -> tool_decision -> tool_execution -> validation -> retry -> risk_check -> human_review -> response_generation"


# ============================================================================
# Convenience Function for Quick Workflow Access
# ============================================================================

def quick_run(user_input: str, user_id: str = "default_user"):
    """
    Quick convenience function to run the workflow with a single input.
    
    Args:
        user_input: User's message
        user_id: User identifier
        
    Returns:
        Workflow response
    """
    from workflows.finance_graph import create_finance_graph
    from state.finance_state import create_initial_state
    
    # Create graph and initial state
    app = create_finance_graph()
    initial_state = create_initial_state(user_id=user_id)
    
    # Add user message
    initial_state["messages"].append({"role": "user", "content": user_input})
    
    # Run workflow
    result = app.invoke(initial_state)
    
    # Extract response
    from utils.message_utils import get_message_content, get_message_role

    assistant_messages = [m for m in result["messages"] if get_message_role(m) == "assistant"]
    response = get_message_content(assistant_messages[-1]) if assistant_messages else "No response generated"
    
    return {
        "response": response,
        "risk_score": result.get("risk_score", 0),
        "needs_review": result.get("needs_human_review", False),
    }


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Main graph components
    "create_finance_graph",
    "get_finance_app",
    "reset_workflow_state",
    "workflow_config",
    "FinanceWorkflowConfig",
    
    # Routing functions
    "route_after_classifier",
    "route_after_planner",
    "route_after_tool_decision",
    "route_after_tool_execution",
    "route_after_validation",
    "route_after_retry",
    "route_after_risk_check",
    "route_after_human_review",
    "route_after_response",
    
    # Helper functions
    "should_execute_more_tools",
    "is_transaction_complete",
    "needs_clarification",
    "get_next_node",
    "print_routing_summary",
    "CONDITIONAL_ROUTES",
    
    # Constants
    "NODE_NAMES",
    "EDGE_TYPES",
    "WORKFLOW_STAGES",
    
    # Utilities
    "WorkflowStateManager",
    "get_workflow_state_manager",
    "validate_workflow",
    "visualize_workflow",
    "WorkflowMetrics",
    "get_workflow_metrics",
    "quick_run",
]


# ============================================================================
# Module Initialization and Testing
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("WORKFLOWS MODULE - FINANCE AGENTIC CHATBOT")
    print("="*70)
    
    # Test 1: Validate workflow
    print("\n1. Validating workflow configuration...")
    validate_workflow()
    
    # Test 2: Print routing summary
    print("\n2. Routing summary:")
    print_routing_summary()
    
    # Test 3: Visualize workflow
    print("\n3. Workflow visualization:")
    visualize_workflow()
    
    # Test 4: Test workflow state manager
    print("\n4. Testing workflow state manager...")
    manager = get_workflow_state_manager()
    manager.start_stage("classifying")
    import time
    time.sleep(0.1)
    manager.end_stage("classifying")
    manager.start_stage("planning")
    time.sleep(0.05)
    manager.end_stage("planning")
    
    summary = manager.get_stage_summary()
    print(f"   Stages completed: {summary['completed_stages']}")
    print(f"   Total duration: {summary['total_duration_seconds']}s")
    
    # Test 5: Quick run test (if graph is available)
    print("\n5. Testing quick_run function...")
    try:
        result = quick_run("What's my balance?", "test_user")
        print(f"   Response: {result['response'][:50]}...")
        print(f"   Risk score: {result['risk_score']}")
    except Exception as e:
        print(f"   Quick run test skipped: {e}")
    
    # Test 6: Export check
    print("\n6. Checking exports...")
    expected_exports = [
        "create_finance_graph",
        "route_after_classifier",
        "route_after_planner",
        "validate_workflow",
        "visualize_workflow",
        "quick_run",
    ]
    
    for export in expected_exports:
        if export in __all__:
            print(f" {export} is exported")
        else:
            print(f" {export} is missing from __all__")
    
    print("\n" + "="*70)
    print(" workflows module is ready to use!")
    print("="*70)
    
    # Print usage examples
    print("\n USAGE EXAMPLES:")
    print("-"*50)
    print("""
    # In your main application:
    from workflows import create_finance_graph, quick_run
    
    # Option 1: Quick run
    result = quick_run("Transfer $500 to savings", user_id="user123")
    
    # Option 2: Full workflow with custom state
    app = create_finance_graph()
    state = create_initial_state(user_id="user123")
    state["messages"].append({"role": "user", "content": "What's my balance?"})
    result = app.invoke(state)
    
    # Option 3: With metrics tracking
    from workflows import get_workflow_metrics
    metrics = get_workflow_metrics()
    print(metrics.get_summary())
    """)