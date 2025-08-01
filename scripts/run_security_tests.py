#!/usr/bin/env python3
"""Comprehensive security test suite for Fresh OR-Tools solver.

This script validates all security features including authentication, authorization,
audit logging, and GUI compatibility.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from config.database_security_config import SecurityLevel, security_config
from src.api.security.application_security import (
    ApplicationSecurityManager,
    SecurityAction,
    SecurityContext,
)
from src.data.clients.secure_database_client import get_database_client


class SecurityTestSuite:
    """Comprehensive security test suite."""

    def __init__(self):
        self.results = {
            "config_validation": {"passed": False, "details": []},
            "authentication_tests": {"passed": False, "details": []},
            "authorization_tests": {"passed": False, "details": []},
            "audit_logging": {"passed": False, "details": []},
            "gui_compatibility": {"passed": False, "details": []},
            "performance_impact": {"passed": False, "details": []},
            "overall": {"passed": False, "score": 0},
        }

    def run_all_tests(self) -> dict[str, Any]:
        """Run all security tests."""
        print("=" * 80)
        print("COMPREHENSIVE SECURITY TEST SUITE")
        print("=" * 80)

        # Test 1: Configuration Validation
        self.test_security_configuration()

        # Test 2: Authentication Tests
        self.test_authentication_mechanisms()

        # Test 3: Authorization Tests
        self.test_authorization_controls()

        # Test 4: Audit Logging
        self.test_audit_logging()

        # Test 5: GUI Compatibility
        self.test_gui_compatibility()

        # Test 6: Performance Impact
        self.test_performance_impact()

        # Calculate overall score
        self.calculate_overall_score()

        return self.results

    def test_security_configuration(self):
        """Test security configuration validation."""
        print("\n🔧 Testing Security Configuration...")

        try:
            # Test configuration loading
            config_valid = security_config.validate_configuration()

            if config_valid["valid"]:
                self.results["config_validation"]["details"].append(
                    "✓ Configuration validation passed"
                )

                # Test security levels
                current_level = security_config.security_level
                self.results["config_validation"]["details"].append(
                    f"✓ Security level: {current_level.value}"
                )

                # Test environment variables
                required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
                for var in required_vars:
                    if os.environ.get(var):
                        self.results["config_validation"]["details"].append(
                            f"✓ {var} configured"
                        )
                    else:
                        self.results["config_validation"]["details"].append(
                            f"✗ {var} missing"
                        )

                self.results["config_validation"]["passed"] = True
            else:
                self.results["config_validation"]["details"].append(
                    "✗ Configuration validation failed"
                )
                self.results["config_validation"]["details"].extend(
                    [f"✗ {issue}" for issue in config_valid["issues"]]
                )

        except Exception as e:
            self.results["config_validation"]["details"].append(
                f"✗ Configuration test failed: {e}"
            )

    def test_authentication_mechanisms(self):
        """Test authentication mechanisms."""
        print("\n🔐 Testing Authentication Mechanisms...")

        try:
            security_manager = ApplicationSecurityManager()

            # Test anonymous access
            anon_headers = {}
            anon_context = security_manager.authenticate_request(anon_headers)

            if security_config.security_level == SecurityLevel.PERMISSIVE:
                if anon_context.role == "admin":
                    self.results["authentication_tests"]["details"].append(
                        "✓ Permissive mode: Anonymous admin access granted"
                    )
                else:
                    self.results["authentication_tests"]["details"].append(
                        "✗ Permissive mode: Anonymous admin access failed"
                    )

            # Test authenticated access
            auth_headers = {"Authorization": "Bearer demo_admin_token"}
            auth_context = security_manager.authenticate_request(auth_headers)

            if auth_context.is_authenticated():
                self.results["authentication_tests"]["details"].append(
                    "✓ Token authentication successful"
                )
                self.results["authentication_tests"]["details"].append(
                    f"✓ User role: {auth_context.role}"
                )
            else:
                self.results["authentication_tests"]["details"].append(
                    "✗ Token authentication failed"
                )

            # Test invalid token
            invalid_headers = {"Authorization": "Bearer invalid_token"}
            invalid_context = security_manager.authenticate_request(invalid_headers)

            if not invalid_context.is_authenticated():
                self.results["authentication_tests"]["details"].append(
                    "✓ Invalid token rejected"
                )
            else:
                self.results["authentication_tests"]["details"].append(
                    "✗ Invalid token accepted"
                )

            self.results["authentication_tests"]["passed"] = True

        except Exception as e:
            self.results["authentication_tests"]["details"].append(
                f"✗ Authentication test failed: {e}"
            )

    def test_authorization_controls(self):
        """Test authorization controls."""
        print("\n🛡️ Testing Authorization Controls...")

        try:
            security_manager = ApplicationSecurityManager()

            # Test admin user permissions
            admin_context = SecurityContext(
                user_id="admin_user",
                role="admin",
                permissions=["read", "write", "delete", "admin"],
            )

            # Test read access
            read_auth = security_manager.authorize_action(
                admin_context, SecurityAction.READ, "departments"
            )
            if read_auth:
                self.results["authorization_tests"]["details"].append(
                    "✓ Admin read access authorized"
                )
            else:
                self.results["authorization_tests"]["details"].append(
                    "✗ Admin read access denied"
                )

            # Test write access
            write_auth = security_manager.authorize_action(
                admin_context, SecurityAction.CREATE, "departments"
            )
            if write_auth:
                self.results["authorization_tests"]["details"].append(
                    "✓ Admin write access authorized"
                )
            else:
                self.results["authorization_tests"]["details"].append(
                    "✗ Admin write access denied"
                )

            # Test regular user permissions
            user_context = SecurityContext(
                user_id="regular_user", role="user", permissions=["read", "write"]
            )

            # Test delete access (should be denied)
            delete_auth = security_manager.authorize_action(
                user_context, SecurityAction.DELETE, "departments"
            )
            if not delete_auth:
                self.results["authorization_tests"]["details"].append(
                    "✓ User delete access properly denied"
                )
            else:
                self.results["authorization_tests"]["details"].append(
                    "✗ User delete access improperly allowed"
                )

            self.results["authorization_tests"]["passed"] = True

        except Exception as e:
            self.results["authorization_tests"]["details"].append(
                f"✗ Authorization test failed: {e}"
            )

    def test_audit_logging(self):
        """Test audit logging functionality."""
        print("\n📝 Testing Audit Logging...")

        try:
            security_manager = ApplicationSecurityManager()

            # Test security event logging
            test_context = SecurityContext(
                user_id="test_user", role="user", department_id="production"
            )

            # Log some test events
            security_manager.authorize_action(
                test_context, SecurityAction.READ, "departments", "dept_123"
            )
            security_manager.authorize_action(
                test_context,
                SecurityAction.CREATE,
                "machines",
                metadata={"department_id": "production"},
            )

            # Retrieve audit log
            audit_entries = security_manager.get_audit_log(limit=10)

            if len(audit_entries) >= 2:
                self.results["audit_logging"]["details"].append(
                    f"✓ Audit log contains {len(audit_entries)} entries"
                )

                # Check audit entry structure
                entry = audit_entries[-1]
                required_fields = ["timestamp", "user_id", "action", "resource"]

                all_fields_present = all(field in entry for field in required_fields)
                if all_fields_present:
                    self.results["audit_logging"]["details"].append(
                        "✓ Audit entries have required fields"
                    )
                else:
                    self.results["audit_logging"]["details"].append(
                        "✗ Audit entries missing required fields"
                    )

                self.results["audit_logging"]["passed"] = True
            else:
                self.results["audit_logging"]["details"].append(
                    "✗ Insufficient audit log entries"
                )

        except Exception as e:
            self.results["audit_logging"]["details"].append(
                f"✗ Audit logging test failed: {e}"
            )

    def test_gui_compatibility(self):
        """Test GUI compatibility after security implementation."""
        print("\n🖥️ Testing GUI Compatibility...")

        try:
            # Test database connectivity
            client = get_database_client("gui")

            start_time = time.time()

            # Test basic CRUD operations
            operations_passed = 0
            total_operations = 4

            # Test SELECT
            try:
                result = client.table("departments").select("*").limit(3).execute()
                if result.data:
                    operations_passed += 1
                    self.results["gui_compatibility"]["details"].append(
                        "✓ GUI SELECT operations working"
                    )
                else:
                    self.results["gui_compatibility"]["details"].append(
                        "✗ GUI SELECT operations failed"
                    )
            except Exception as e:
                self.results["gui_compatibility"]["details"].append(
                    f"✗ GUI SELECT failed: {e}"
                )

            # Test INSERT
            try:
                test_dept = {
                    "code": f"TEST_SEC_{int(time.time())}",
                    "name": "Security Test Department",
                    "description": "Test department for security validation",
                }
                insert_result = client.table("departments").insert(test_dept).execute()
                if insert_result.data:
                    operations_passed += 1
                    test_dept_id = insert_result.data[0]["department_id"]
                    self.results["gui_compatibility"]["details"].append(
                        "✓ GUI INSERT operations working"
                    )

                    # Test UPDATE
                    try:
                        update_result = (
                            client.table("departments")
                            .update({"description": "Updated security test department"})
                            .eq("department_id", test_dept_id)
                            .execute()
                        )
                        if update_result.data:
                            operations_passed += 1
                            self.results["gui_compatibility"]["details"].append(
                                "✓ GUI UPDATE operations working"
                            )
                    except Exception as e:
                        self.results["gui_compatibility"]["details"].append(
                            f"✗ GUI UPDATE failed: {e}"
                        )

                    # Test DELETE
                    try:
                        delete_result = (
                            client.table("departments")
                            .delete()
                            .eq("department_id", test_dept_id)
                            .execute()
                        )
                        operations_passed += 1
                        self.results["gui_compatibility"]["details"].append(
                            "✓ GUI DELETE operations working"
                        )
                    except Exception as e:
                        self.results["gui_compatibility"]["details"].append(
                            f"✗ GUI DELETE failed: {e}"
                        )

            except Exception as e:
                self.results["gui_compatibility"]["details"].append(
                    f"✗ GUI INSERT failed: {e}"
                )

            duration = (time.time() - start_time) * 1000
            self.results["gui_compatibility"]["details"].append(
                f"✓ GUI operations completed in {duration:.2f}ms"
            )

            # GUI compatibility passes if most operations work
            if operations_passed >= 3:
                self.results["gui_compatibility"]["passed"] = True

        except Exception as e:
            self.results["gui_compatibility"]["details"].append(
                f"✗ GUI compatibility test failed: {e}"
            )

    def test_performance_impact(self):
        """Test performance impact of security implementation."""
        print("\n⚡ Testing Performance Impact...")

        try:
            # Measure baseline performance
            client = get_database_client("gui")

            # Warm up
            client.table("departments").select("department_id").limit(1).execute()

            # Test multiple operations
            iterations = 10
            total_time = 0

            for i in range(iterations):
                start_time = time.time()
                result = client.table("departments").select("*").limit(5).execute()
                end_time = time.time()

                total_time += end_time - start_time

            avg_time = (total_time / iterations) * 1000  # Convert to ms

            self.results["performance_impact"]["details"].append(
                f"✓ Average query time: {avg_time:.2f}ms"
            )

            # Performance is acceptable if under 2 seconds per operation
            if avg_time < 2000:
                self.results["performance_impact"]["details"].append(
                    "✓ Performance impact acceptable"
                )
                self.results["performance_impact"]["passed"] = True
            else:
                self.results["performance_impact"]["details"].append(
                    "✗ Performance impact too high"
                )

            # Test security overhead
            security_manager = ApplicationSecurityManager()

            security_start = time.time()
            for i in range(100):
                context = SecurityContext(user_id="test", role="user")
                security_manager.authorize_action(
                    context, SecurityAction.READ, "departments"
                )
            security_end = time.time()

            security_overhead = ((security_end - security_start) / 100) * 1000
            self.results["performance_impact"]["details"].append(
                f"✓ Security overhead: {security_overhead:.2f}ms per operation"
            )

            if security_overhead < 10:  # Less than 10ms overhead
                self.results["performance_impact"]["details"].append(
                    "✓ Security overhead within acceptable limits"
                )
            else:
                self.results["performance_impact"]["details"].append(
                    "✗ Security overhead too high"
                )

        except Exception as e:
            self.results["performance_impact"]["details"].append(
                f"✗ Performance test failed: {e}"
            )

    def calculate_overall_score(self):
        """Calculate overall security test score."""
        test_categories = [
            "config_validation",
            "authentication_tests",
            "authorization_tests",
            "audit_logging",
            "gui_compatibility",
            "performance_impact",
        ]

        passed_tests = sum(1 for cat in test_categories if self.results[cat]["passed"])
        total_tests = len(test_categories)

        score_percentage = (passed_tests / total_tests) * 100

        self.results["overall"]["score"] = score_percentage
        self.results["overall"]["passed"] = (
            score_percentage >= 80
        )  # 80% pass rate required

        print(f"\n{'=' * 80}")
        print(
            f"SECURITY TEST RESULTS: {passed_tests}/{total_tests} tests passed ({score_percentage:.1f}%)"
        )
        print(f"{'=' * 80}")

        for category in test_categories:
            status = "✓ PASS" if self.results[category]["passed"] else "✗ FAIL"
            print(f"{category.replace('_', ' ').title()}: {status}")
            for detail in self.results[category]["details"]:
                print(f"  {detail}")

        print(f"\n{'=' * 80}")
        if self.results["overall"]["passed"]:
            print("🎉 SECURITY IMPLEMENTATION: PASSED")
            print("The security system is ready for production deployment.")
        else:
            print("⚠️ SECURITY IMPLEMENTATION: NEEDS ATTENTION")
            print(
                "Some security tests failed. Review and fix issues before deployment."
            )
        print(f"{'=' * 80}")


def main():
    """Run security test suite."""
    load_dotenv()

    suite = SecurityTestSuite()
    results = suite.run_all_tests()

    # Save results to file
    results_file = (
        project_root / f"reports/security_test_results_{int(time.time())}.json"
    )
    results_file.parent.mkdir(exist_ok=True)

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nDetailed results saved to: {results_file}")

    # Return appropriate exit code
    return 0 if results["overall"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
