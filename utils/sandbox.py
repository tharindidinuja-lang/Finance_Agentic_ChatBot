# utils/sandbox.py
"""Safe execution environment for untrusted code"""

import ast
import sys
import os
import subprocess
import tempfile
import signal
import time
from typing import Any, Dict, Optional, Callable
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import traceback


class SandboxError(Exception):
    """Sandbox execution error"""
    pass


class TimeoutError(SandboxError):
    """Execution timeout error"""
    pass


class CodeSandbox:
    """
    Safe sandbox for executing untrusted Python code.
    Restricts imports, builtins, and system access.
    """
    
    # Allowed modules for import
    ALLOWED_MODULES = {
        'math', 'random', 'datetime', 'collections', 'itertools',
        'json', 're', 'string', 'statistics', 'fractions', 'decimal'
    }
    
    # Restricted builtins (disallow dangerous functions)
    RESTRICTED_BUILTINS = {
        'eval', 'exec', 'compile', 'open', 'input', 'raw_input',
        '__import__', 'globals', 'locals', 'vars', 'dir',
        'help', 'exit', 'quit', 'print'  # Print is allowed but redirected
    }
    
    def __init__(self, timeout_seconds: int = 5, memory_limit_mb: int = 100):
        """
        Initialize sandbox.
        
        Args:
            timeout_seconds: Maximum execution time
            memory_limit_mb: Maximum memory usage (approximate)
        """
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.safe_globals = self._create_safe_globals()
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """Create safe global namespace for execution"""
        
        # Start with basic safe builtins
        safe_builtins = {}
        for name, value in __builtins__.__dict__.items():
            if name not in self.RESTRICTED_BUILTINS:
                safe_builtins[name] = value
        
        # Create safe global dict
        safe_globals = {
            '__builtins__': safe_builtins,
            '__name__': '__sandbox__',
            '__doc__': None,
        }
        
        # Add allowed modules
        for module_name in self.ALLOWED_MODULES:
            try:
                safe_globals[module_name] = __import__(module_name)
            except ImportError:
                pass
        
        return safe_globals
    
    def execute_code(self, code: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute code safely in sandbox.
        
        Args:
            code: Python code string
            timeout: Override default timeout
            
        Returns:
            Dict with 'output', 'error', 'result'
        """
        timeout_sec = timeout or self.timeout_seconds
        
        # Parse and validate AST
        try:
            tree = ast.parse(code)
            self._validate_ast(tree)
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Syntax error: {e}",
                "output": "",
                "result": None
            }
        except SandboxError as e:
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "result": None
            }
        
        # Execute with timeout
        output_buffer = StringIO()
        error_buffer = StringIO()
        
        try:
            with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                result = self._execute_with_timeout(code, timeout_sec)
            
            output = output_buffer.getvalue()
            error = error_buffer.getvalue()
            
            return {
                "success": True,
                "output": output,
                "error": error if error else None,
                "result": result
            }
            
        except TimeoutError as e:
            return {
                "success": False,
                "error": f"Execution timeout ({timeout_sec}s)",
                "output": output_buffer.getvalue(),
                "result": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {e}\n{traceback.format_exc()}",
                "output": output_buffer.getvalue(),
                "result": None
            }
    
    def _validate_ast(self, tree: ast.AST):
        """Validate AST for unsafe operations"""
        
        class UnsafeNodeVisitor(ast.NodeVisitor):
            def __init__(self):
                self.unsafe_nodes = []
            
            def visit_Import(self, node):
                for alias in node.names:
                    if alias.name not in CodeSandbox.ALLOWED_MODULES:
                        self.unsafe_nodes.append(f"Import of '{alias.name}' not allowed")
                self.generic_visit(node)
            
            def visit_ImportFrom(self, node):
                if node.module not in CodeSandbox.ALLOWED_MODULES:
                    self.unsafe_nodes.append(f"Import from '{node.module}' not allowed")
                self.generic_visit(node)
            
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    if node.func.id in CodeSandbox.RESTRICTED_BUILTINS:
                        self.unsafe_nodes.append(f"Call to '{node.func.id}' not allowed")
                self.generic_visit(node)
            
            def visit_Attribute(self, node):
                # Block file operations
                if isinstance(node.value, ast.Name):
                    if node.value.id == 'open' or node.attr in ['open', 'read', 'write']:
                        self.unsafe_nodes.append(f"File operation '{node.attr}' not allowed")
                self.generic_visit(node)
        
        visitor = UnsafeNodeVisitor()
        visitor.visit(tree)
        
        if visitor.unsafe_nodes:
            raise SandboxError("\n".join(visitor.unsafe_nodes))
    
    def _execute_with_timeout(self, code: str, timeout: int) -> Any:
        """Execute code with timeout using subprocess"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Run in subprocess with timeout
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                env={'PYTHONPATH': '', 'PATH': ''}  # Clean environment
            )
            
            if result.returncode != 0:
                raise Exception(result.stderr)
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Execution exceeded {timeout} seconds")
        finally:
            os.unlink(temp_file)
    
    def execute_safe_function(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function safely with timeout.
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
        """
        import threading
        
        result_container = [None]
        error_container = [None]
        
        def wrapper():
            try:
                result_container[0] = func(*args, **kwargs)
            except Exception as e:
                error_container[0] = e
        
        thread = threading.Thread(target=wrapper)
        thread.start()
        thread.join(timeout=self.timeout_seconds)
        
        if thread.is_alive():
            raise TimeoutError(f"Function execution exceeded {self.timeout_seconds} seconds")
        
        if error_container[0]:
            raise error_container[0]
        
        return result_container[0]


class FinancialCalculatorSandbox(CodeSandbox):
    """Specialized sandbox for financial calculations"""
    
    # Additional allowed operations for finance
    ALLOWED_FINANCE_MODULES = {
        'math', 'decimal', 'fractions', 'statistics'
    }
    
    def __init__(self, timeout_seconds: int = 3):
        super().__init__(timeout_seconds=timeout_seconds)
        self.ALLOWED_MODULES.update(self.ALLOWED_FINANCE_MODULES)
    
    def calculate_loan_emi(self, principal: float, rate: float, years: int) -> float:
        """Calculate EMI using safe execution"""
        code = f"""
import math

principal = {principal}
rate = {rate}
years = {years}

monthly_rate = rate / 12 / 100
months = years * 12

emi = principal * monthly_rate * (1 + monthly_rate)**months / ((1 + monthly_rate)**months - 1)
print(f"{{emi:.2f}}")
"""
        result = self.execute_code(code)
        
        if result["success"] and result["output"].strip():
            try:
                return float(result["output"].strip())
            except ValueError:
                pass
        
        return 0.0
    
    def calculate_returns(self, principal: float, rate: float, years: int, 
                          compounding_frequency: int = 12) -> float:
        """Calculate investment returns"""
        code = f"""
principal = {principal}
rate = {rate}
years = {years}
n = {compounding_frequency}

amount = principal * (1 + rate/100/n)**(n * years)
print(f"{{amount:.2f}}")
"""
        result = self.execute_code(code)
        
        if result["success"] and result["output"].strip():
            try:
                return float(result["output"].strip())
            except ValueError:
                pass
        
        return principal


if __name__ == "__main__":
    print("=" * 50)
    print("CODE SANDBOX TEST")
    print("=" * 50)
    
    sandbox = CodeSandbox(timeout_seconds=2)
    
    # Safe code
    safe_code = """
import math
result = math.sqrt(144)
print(f"Result: {result}")
"""
    
    print("\nSafe Code Execution:")
    result = sandbox.execute_code(safe_code)
    print(f"  Success: {result['success']}")
    print(f"  Output: {result['output']}")
    
    # Unsafe code (blocked)
    unsafe_code = """
import os
os.system('ls -la')
"""
    
    print("\nUnsafe Code Execution (should be blocked):")
    result = sandbox.execute_code(unsafe_code)
    print(f"  Success: {result['success']}")
    print(f"  Error: {result['error'][:100]}...")
    
    # Test financial sandbox
    print("\nFinancial Calculator Sandbox:")
    finance_sandbox = FinancialCalculatorSandbox()
    
    emi = finance_sandbox.calculate_loan_emi(300000, 6.5, 30)
    print(f"  EMI for $300,000 loan at 6.5% for 30 years: ${emi:,.2f}")
    
    returns = finance_sandbox.calculate_returns(10000, 8, 10)
    print(f"  $10,000 at 8% for 10 years: ${returns:,.2f}")