#!/usr/bin/env python3
"""
Test runner for trivia application
Runs all test files in the tests/ directory
"""

import subprocess
import sys
import os
from pathlib import Path

def run_test(test_file):
    """Run a single test file and return success status"""
    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=False, 
                              text=True, 
                              check=True)
        print(f"✅ {test_file} PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {test_file} FAILED")
        return False
    except Exception as e:
        print(f"❌ {test_file} ERROR: {e}")
        return False

def main():
    """Run all tests in the tests directory"""
    tests_dir = Path("tests")
    
    if not tests_dir.exists():
        print("❌ Tests directory not found!")
        return 1
    
    # Find all Python test files
    test_files = list(tests_dir.glob("test_*.py"))
    
    if not test_files:
        print("❌ No test files found!")
        return 1
    
    print(f"Found {len(test_files)} test files")
    
    # Run each test
    passed = 0
    failed = 0
    
    for test_file in sorted(test_files):
        if run_test(test_file):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n💥 {failed} TEST(S) FAILED!")
        return 1

if __name__ == "__main__":
    exit(main())