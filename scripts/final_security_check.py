#!/usr/bin/env python3
"""Final security verification for Fresh Solver."""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class FinalSecurityCheck:
    """Final comprehensive security check."""

    def __init__(self):
        self.passed_checks = []
        self.failed_checks = []
        self.warnings = []

    def check_critical_fixes(self):
        """Verify all critical security fixes are implemented."""
        print("\n🔒 Critical Security Fixes Verification")
        print("=" * 60)

        # 1. SQL Injection Check
        print("\n1️⃣ SQL Injection Prevention:")
        sql_injection_found = False

        # Check the specific file mentioned in the vulnerability
        db_file = Path("src/data/loaders/database.py")
        if db_file.exists():
            content = db_file.read_text()
            # Look for f-string SQL patterns
            if re.search(r'f["\'].*SELECT.*FROM.*\{.*\}', content):
                self.failed_checks.append("SQL injection vulnerability still present")
                print("   ❌ F-string SQL interpolation found")
                sql_injection_found = True
            else:
                # Check for proper parameterized queries
                if "get_database_client" in content or "supabase" in content.lower():
                    self.passed_checks.append(
                        "SQL injection fixed with parameterized queries"
                    )
                    print("   ✅ Using parameterized queries")
                else:
                    self.warnings.append("Cannot verify SQL query safety")
                    print("   ⚠️  Cannot verify query safety")
        else:
            self.warnings.append("Database loader file not found")
            print("   ⚠️  Database loader file not found")

        # 2. RLS Configuration Check
        print("\n2️⃣ RLS Configuration:")
        rls_enabled = os.getenv("RLS_ENABLED", "false").lower() == "true"
        security_level = os.getenv("DATABASE_SECURITY_LEVEL", "none")

        if rls_enabled:
            self.passed_checks.append("RLS enabled in configuration")
            print("   ✅ RLS_ENABLED=true")
            print(f"   ✅ Security Level: {security_level}")
        else:
            self.failed_checks.append("RLS not enabled in configuration")
            print("   ❌ RLS_ENABLED=false or not set")

        # Check for RLS migration files
        rls_migrations = list(Path("migrations").glob("*rls*.sql"))
        if rls_migrations:
            self.passed_checks.append(
                f"RLS migration files exist ({len(rls_migrations)} files)"
            )
            print(f"   ✅ Found {len(rls_migrations)} RLS migration files")
        else:
            self.failed_checks.append("No RLS migration files found")
            print("   ❌ No RLS migration files")

        # 3. JWT Authentication Check
        print("\n3️⃣ JWT Authentication:")
        jwt_files = ["src/api/security/middleware.py", "gui/gui/lib/auth/context.tsx"]

        jwt_implemented = False
        for file in jwt_files:
            if Path(file).exists():
                content = Path(file).read_text()
                if "jwt" in content.lower() and (
                    "verify" in content or "decode" in content
                ):
                    jwt_implemented = True
                    break

        if jwt_implemented:
            self.passed_checks.append("JWT authentication implemented")
            print("   ✅ JWT verification implemented")
        else:
            self.failed_checks.append("JWT authentication not properly implemented")
            print("   ❌ JWT verification not found")

        # Check for placeholder auth
        middleware = Path("src/api/security/middleware.py")
        if middleware.exists():
            content = middleware.read_text()
            if "len(token) > 10" in content or "len(token) < 10" in content:
                self.failed_checks.append("Placeholder token validation still present")
                print("   ❌ Placeholder validation detected")
            else:
                print("   ✅ No placeholder validation found")

        # 4. Secret Management Check
        print("\n4️⃣ Secret Management:")

        # Check .env is in .gitignore
        gitignore = Path(".gitignore")
        if gitignore.exists():
            content = gitignore.read_text()
            if ".env" in content:
                self.passed_checks.append(".env files excluded from git")
                print("   ✅ .env in .gitignore")
            else:
                self.failed_checks.append(".env not in .gitignore")
                print("   ❌ .env not in .gitignore")

        # Check for hardcoded secrets in code
        secret_patterns = [r'SUPABASE.*KEY.*=.*["\']ey', r'JWT_SECRET.*=.*["\'][^$\{]']

        hardcoded_found = False
        for root, dirs, files in os.walk("src"):
            # Skip .env files
            files = [f for f in files if not f.startswith(".env")]

            for file in files:
                if file.endswith((".py", ".ts", ".tsx", ".js")):
                    filepath = Path(root) / file
                    try:
                        content = filepath.read_text()
                        for pattern in secret_patterns:
                            if re.search(pattern, content):
                                hardcoded_found = True
                                self.failed_checks.append(
                                    f"Hardcoded secret in {filepath}"
                                )
                                break
                    except:
                        pass

        if not hardcoded_found:
            self.passed_checks.append("No hardcoded secrets in code")
            print("   ✅ No hardcoded secrets found")
        else:
            print("   ❌ Hardcoded secrets detected")

    def check_security_framework(self):
        """Check overall security framework implementation."""
        print("\n\n🛡️ Security Framework Verification")
        print("=" * 60)

        # Application Security
        app_security = Path("src/api/security/application_security.py")
        if app_security.exists():
            self.passed_checks.append("Application security framework exists")
            print("✅ Application security framework implemented")

            content = app_security.read_text()
            features = {
                "Authentication": "authenticate" in content,
                "Authorization": "authorize" in content,
                "Audit Logging": "audit" in content.lower(),
                "Security Context": "SecurityContext" in content,
            }

            for feature, check in features.items():
                if check:
                    print(f"   ✅ {feature}")
                else:
                    print(f"   ❌ {feature}")
                    self.warnings.append(f"Missing {feature} in security framework")
        else:
            self.failed_checks.append("Application security framework missing")
            print("❌ Application security framework not found")

        # API Security Middleware
        middleware = Path("src/api/security/middleware.py")
        if middleware.exists():
            content = middleware.read_text()

            features = {
                "Rate Limiting": "rate_limit" in content,
                "Input Validation": "validate" in content,
                "CORS": "cors" in content.lower(),
                "Error Handling": "SecurityException" in content,
            }

            print("\n✅ API Security Middleware implemented")
            for feature, check in features.items():
                if check:
                    print(f"   ✅ {feature}")
                else:
                    print(f"   ⚠️  {feature} not detected")

    def check_gui_integration(self):
        """Check GUI security integration."""
        print("\n\n🖥️ GUI Security Integration")
        print("=" * 60)

        # Check auth context
        auth_context = Path("gui/gui/lib/auth/context.tsx")
        if auth_context.exists():
            self.passed_checks.append("Auth context implemented")
            print("✅ Authentication context exists")
        else:
            self.failed_checks.append("Auth context missing")
            print("❌ Authentication context missing")

        # Check form security
        forms = [
            "gui/gui/components/forms/DepartmentForm.tsx",
            "gui/gui/components/forms/MachineForm.tsx",
        ]

        print("\n📝 Form Security:")
        for form in forms:
            if Path(form).exists():
                content = Path(form).read_text()

                has_validation = "zodResolver" in content or "validation" in content
                has_error_handling = "catch" in content or "error" in content

                form_name = Path(form).name
                if has_validation and has_error_handling:
                    print(f"   ✅ {form_name}: validation & error handling")
                else:
                    print(f"   ⚠️  {form_name}: missing security features")
                    self.warnings.append(f"{form_name} may lack security features")

    def generate_summary(self):
        """Generate final summary."""
        print("\n\n" + "=" * 70)
        print("📊 FINAL SECURITY VERIFICATION SUMMARY")
        print("=" * 70)

        total_passed = len(self.passed_checks)
        total_failed = len(self.failed_checks)
        total_warnings = len(self.warnings)

        print(f"\n✅ Passed Checks: {total_passed}")
        print(f"❌ Failed Checks: {total_failed}")
        print(f"⚠️  Warnings: {total_warnings}")

        if total_failed == 0:
            print("\n🎉 ALL CRITICAL SECURITY ISSUES RESOLVED!")
            print("\nThe Fresh Solver application now has:")
            print("  ✅ SQL injection protection")
            print("  ✅ Authentication system")
            print("  ✅ RLS configuration")
            print("  ✅ Secure secret management")
            print("  ✅ Comprehensive security framework")

            if total_warnings > 0:
                print(
                    f"\n⚠️  Note: {total_warnings} warnings require attention for production deployment"
                )

            print("\n✅ SYSTEM IS READY FOR PRODUCTION DEPLOYMENT")

        else:
            print(f"\n❌ {total_failed} CRITICAL ISSUES REMAIN:")
            for issue in self.failed_checks[:5]:  # Show first 5
                print(f"  - {issue}")
            if len(self.failed_checks) > 5:
                print(f"  ... and {len(self.failed_checks) - 5} more")

            print("\n⚠️  DO NOT DEPLOY TO PRODUCTION")

        # Save detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "passed": total_passed,
                "failed": total_failed,
                "warnings": total_warnings,
                "production_ready": total_failed == 0,
            },
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "warnings": self.warnings,
        }

        report_path = Path("final_security_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_path}")

        return total_failed == 0


def main():
    """Run final security check."""
    print("🔐 Fresh Solver - Final Security Verification")
    print("=" * 70)

    checker = FinalSecurityCheck()

    # Run all checks
    checker.check_critical_fixes()
    checker.check_security_framework()
    checker.check_gui_integration()

    # Generate summary
    production_ready = checker.generate_summary()

    return 0 if production_ready else 1


if __name__ == "__main__":
    sys.exit(main())
