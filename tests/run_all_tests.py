#!/usr/bin/env python3
"""
Test runner for all AI_Slop tests.
Run with: python tests/run_all_tests.py

Test Structure:
- tests/AI_Slop/        - Unit tests for AI_Slop modules  
- tests/integration/    - Integration tests with mock/real data
"""

import unittest
import sys
import os
from datetime import datetime

# Add the project directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def run_unit_tests():
    """Run unit tests for AI_Slop modules"""
    print("🔬 Running Unit Tests (AI_Slop modules)...")
    
    test_dir = os.path.join(os.path.dirname(__file__), 'AI_Slop')
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_integration_tests():
    """Run integration tests"""
    print("\n🔗 Running Integration Tests...")
    
    test_dir = os.path.join(os.path.dirname(__file__), 'integration')
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_frontend_tests():
    """Run frontend and Django view tests"""
    print("\n🌐 Running Frontend Tests...")
    
    test_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_legacy_tests():
    """Run legacy function-based tests for compatibility"""
    print("\n🔄 Running Legacy Tests...")
    
    # Import legacy test functions
    test_modules = []
    
    try:
        from tests.AI_Slop.test_llm_client import test_llm_client, test_orchestrator, test_provider_switching, check_environment
        test_modules.append(("Environment Check", check_environment))
        test_modules.append(("LLM Client", test_llm_client))
        test_modules.append(("Orchestrator LLM", test_orchestrator))
        test_modules.append(("Provider Switching", test_provider_switching))
    except ImportError as e:
        print(f"⚠️  Could not import LLM client tests: {e}")
    
    try:
        from tests.AI_Slop.test_jsearch_client import test_jsearch_integration
        test_modules.append(("JSearch API", test_jsearch_integration))
    except ImportError as e:
        print(f"⚠️  Could not import JSearch tests: {e}")
    
    try:
        from tests.AI_Slop.test_agents import test_spreadsheet_export
        test_modules.append(("Spreadsheet Export", test_spreadsheet_export))
    except ImportError as e:
        print(f"⚠️  Could not import agent tests: {e}")
    
    try:
        from tests.AI_Slop.test_orchestrator import test_orchestrator_workflow
        test_modules.append(("Full Workflow", test_orchestrator_workflow))
    except ImportError as e:
        print(f"⚠️  Could not import orchestrator tests: {e}")
    
    if not test_modules:
        print("⚠️ No legacy test modules found")
        return True
    
    # Run legacy tests
    results = []
    for test_name, test_func in test_modules:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Check if all legacy tests passed
    return all(success for _, success in results)

def run_all_tests():
    """Discover and run all tests in organized structure"""
    
    print("🧪 AI_Slop Test Suite")
    print("=" * 60)
    
    # Run unit tests first
    unit_success = run_unit_tests()
    
    # Run integration tests
    integration_success = run_integration_tests()
    
    # Run frontend tests
    frontend_success = run_frontend_tests()
    
    # Run legacy tests for compatibility
    legacy_success = run_legacy_tests()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"  Unit Tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
    print(f"  Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    print(f"  Frontend Tests: {'✅ PASSED' if frontend_success else '❌ FAILED'}")
    print(f"  Legacy Tests: {'✅ PASSED' if legacy_success else '❌ FAILED'}")
    
    overall_success = unit_success and integration_success and frontend_success and legacy_success
    
    if overall_success:
        print(f"\n🎉 All tests passed! System is working correctly.")
        print(f"🚀 Ready to run: python manage.py runserver")
    else:
        print(f"\n⚠️  Some tests failed. Check configuration.")
        print(f"📖 See SETUP.md for troubleshooting guide.")
    
    return overall_success

if __name__ == '__main__':
    print(f"Starting test suite at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    success = run_all_tests()
    
    print(f"\nTest suite completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)