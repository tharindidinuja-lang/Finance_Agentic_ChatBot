# tests/run_all_tests.py
"""Run all tests for Finance Agentic Chatbot"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_all_tests():
    """Run all test suites"""
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n ALL TESTS PASSED!")
    else:
        print("\n SOME TESTS FAILED!")
        
        # Print failures
        if result.failures:
            print("\n--- FAILURES ---")
            for failure in result.failures:
                print(f"\n{failure[0]}")
                print(failure[1])
        
        # Print errors
        if result.errors:
            print("\n--- ERRORS ---")
            for error in result.errors:
                print(f"\n{error[0]}")
                print(error[1])
    
    return result.wasSuccessful()


def run_test_module(module_name: str):
    """Run a specific test module"""
    suite = unittest.defaultTestLoader.loadTestsFromName(module_name)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Finance Agent tests")
    parser.add_argument(
        "--module", 
        type=str, 
        help="Specific test module to run (e.g., test_nodes.test_classifier)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if args.module:
        success = run_test_module(args.module)
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)