#!/usr/bin/env python3
"""
Test runner for health endpoint and AI functionality tests
"""

import sys
import os
import subprocess
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def run_tests():
    """Run all health-related tests"""
    
    test_files = [
        "tests/test_health_simple.py",
        "tests/test_health_endpoint.py", 
        "tests/test_health_integration.py",
        "tests/test_mcp_process_scenarios.py",
        "tests/test_ai_endpoints.py",
        "tests/test_ai_security.py"
    ]
    
    print("🧪 Running Health Endpoint and AI Tests")
    print("=" * 50)
    
    all_passed = True
    
    for test_file in test_files:
        test_path = backend_dir / test_file
        
        if not test_path.exists():
            print(f"⚠️  Test file not found: {test_file}")
            continue
            
        print(f"\n📋 Running {test_file}...")
        
        try:
            # Run pytest on the specific file
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(test_path),
                "-v",
                "--tb=short",
                "--no-header"
            ], capture_output=True, text=True, cwd=backend_dir)
            
            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
                # Print summary of passed tests
                lines = result.stdout.split('\n')
                passed_tests = [line for line in lines if '::' in line and 'PASSED' in line]
                print(f"   {len(passed_tests)} tests passed")
            else:
                print(f"❌ {test_file} - FAILED")
                all_passed = False
                
                # Print error details
                if result.stdout:
                    print("STDOUT:")
                    print(result.stdout)
                if result.stderr:
                    print("STDERR:")
                    print(result.stderr)
                    
        except Exception as e:
            print(f"❌ Error running {test_file}: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All health tests PASSED!")
        print("\n✨ AI Teammate's 'senses' are working perfectly!")
        print("   - Health endpoint provides rich system insights")
        print("   - AI can analyze system status and suggest actions")
        print("   - Security controls prevent unauthorized operations")
        print("   - MCP server monitoring detects issues proactively")
    else:
        print("💥 Some tests FAILED!")
        print("   Check the error messages above for details.")
        return 1
    
    return 0

def run_specific_test_category(category):
    """Run tests for a specific category"""
    
    categories = {
        'health': ['tests/test_health_simple.py', 'tests/test_health_endpoint.py'],
        'integration': ['tests/test_health_integration.py'],
        'mcp': ['tests/test_mcp_process_scenarios.py'],
        'ai': ['tests/test_ai_endpoints.py', 'tests/test_ai_security.py'],
        'all': None  # Will run all tests
    }
    
    if category not in categories:
        print(f"❌ Unknown category: {category}")
        print(f"Available categories: {', '.join(categories.keys())}")
        return 1
    
    if category == 'all':
        return run_tests()
    
    test_files = categories[category]
    
    print(f"🧪 Running {category.upper()} tests")
    print("=" * 30)
    
    for test_file in test_files:
        test_path = backend_dir / test_file
        
        if not test_path.exists():
            print(f"⚠️  Test file not found: {test_file}")
            continue
            
        print(f"\n📋 Running {test_file}...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(test_path),
                "-v"
            ], cwd=backend_dir)
            
            if result.returncode != 0:
                return 1
                
        except Exception as e:
            print(f"❌ Error running {test_file}: {e}")
            return 1
    
    print(f"\n🎉 All {category} tests PASSED!")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        category = sys.argv[1]
        exit_code = run_specific_test_category(category)
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)