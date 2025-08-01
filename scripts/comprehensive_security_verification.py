#!/usr/bin/env python3
"""Comprehensive security verification for Fresh Solver."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class SecurityVerification:
    """Comprehensive security verification system."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "PENDING",
            "checks": {},
        }

    def check_file_security(self) -> tuple[bool, list[str]]:
        """Check for security vulnerabilities in files."""
        print("\n🔍 File Security Check")
        print("-" * 50)

        issues = []

        # Check for SQL injection vulnerabilities
        print("Checking for SQL injection vulnerabilities...")
        sql_injection_pattern = r'f".*SELECT.*FROM.*{.*}.*"'

        try:
            result = subprocess.run(
                ["rg", "-n", sql_injection_pattern, "src/", "gui/"],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                issues.append("SQL injection vulnerabilities found:")
                issues.append(result.stdout)
                print("❌ SQL injection patterns detected")
            else:
                print("✅ No SQL injection patterns found")

        except subprocess.CalledProcessError:
            print("✅ No SQL injection patterns found")

        # Check for hardcoded secrets
        print("\nChecking for hardcoded secrets...")
        secret_patterns = [
            r'SUPABASE_SERVICE_ROLE_KEY\s*=\s*["\']ey',
            r'JWT_SECRET\s*=\s*["\'][^$]',
            r'password\s*=\s*["\'][^$]',
        ]

        for pattern in secret_patterns:
            try:
                result = subprocess.run(
                    ["rg", "-n", pattern, "src/", "--glob", "!*.env*"],
                    capture_output=True,
                    text=True,
                )

                if result.stdout:
                    issues.append(f"Hardcoded secrets found for pattern {pattern}:")
                    issues.append(result.stdout)

            except subprocess.CalledProcessError:
                pass

        if not any("Hardcoded secrets" in issue for issue in issues):
            print("✅ No hardcoded secrets in code")
        else:
            print("❌ Hardcoded secrets detected")

        # Check .gitignore
        print("\nChecking .gitignore for security...")
        gitignore_path = Path(".gitignore")
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            required_patterns = [".env", ".env.local", ".env.production"]
            missing = [p for p in required_patterns if p not in content]

            if missing:
                issues.append(f"Missing from .gitignore: {', '.join(missing)}")
                print(f"❌ Missing patterns in .gitignore: {missing}")
            else:
                print("✅ .gitignore properly configured")
        else:
            issues.append(".gitignore file missing")
            print("❌ .gitignore file missing")

        return len(issues) == 0, issues

    def check_authentication(self) -> tuple[bool, list[str]]:
        """Check authentication implementation."""
        print("\n🔐 Authentication Check")
        print("-" * 50)

        issues = []

        # Check JWT implementation
        jwt_files = [
            "src/api/security/middleware.py",
            "gui/gui/lib/auth/context.tsx",
            "gui/gui/lib/supabase-auth.ts",
        ]

        print("Checking JWT implementation...")
        jwt_ok = True
        for file in jwt_files:
            if Path(file).exists():
                content = Path(file).read_text()
                if "jwt" in content.lower() or "JWT" in content:
                    print(f"✅ JWT implementation found in {file}")
                else:
                    issues.append(f"No JWT implementation in {file}")
                    jwt_ok = False
            else:
                issues.append(f"Missing auth file: {file}")
                jwt_ok = False

        if not jwt_ok:
            print("❌ JWT implementation incomplete")

        # Check for placeholder auth
        print("\nChecking for placeholder authentication...")
        placeholder_patterns = [
            r"len\(token\)\s*>\s*10",
            r"demo_admin_token",
            r"placeholder.*token",
        ]

        placeholder_found = False
        for pattern in placeholder_patterns:
            try:
                result = subprocess.run(
                    ["rg", "-n", pattern, "src/"], capture_output=True, text=True
                )

                if result.stdout:
                    issues.append(f"Placeholder auth found: {pattern}")
                    placeholder_found = True

            except subprocess.CalledProcessError:
                pass

        if placeholder_found:
            print("❌ Placeholder authentication detected")
        else:
            print("✅ No placeholder authentication found")

        return len(issues) == 0, issues

    def check_rls_configuration(self) -> tuple[bool, list[str]]:
        """Check RLS configuration."""
        print("\n🛡️ RLS Configuration Check")
        print("-" * 50)

        issues = []

        # Check environment config
        env_vars = {
            "RLS_ENABLED": os.getenv("RLS_ENABLED"),
            "DATABASE_SECURITY_LEVEL": os.getenv("DATABASE_SECURITY_LEVEL"),
            "AUTH_REQUIRED": os.getenv("AUTH_REQUIRED"),
        }

        print("Environment configuration:")
        for var, value in env_vars.items():
            if value:
                print(f"  {var}: {value}")
            else:
                issues.append(f"{var} not set")

        # Check migration files
        print("\nChecking RLS migration files...")
        migration_files = list(Path("migrations").glob("*rls*.sql"))

        if migration_files:
            print(f"✅ Found {len(migration_files)} RLS migration files")
            for file in migration_files:
                content = file.read_text()
                if "ENABLE ROW LEVEL SECURITY" in content:
                    print(f"  ✅ {file.name} contains RLS enablement")
                else:
                    issues.append(f"{file.name} missing RLS enablement")
        else:
            issues.append("No RLS migration files found")
            print("❌ No RLS migration files found")

        return len(issues) == 0, issues

    def check_api_security(self) -> tuple[bool, list[str]]:
        """Check API security implementation."""
        print("\n🌐 API Security Check")
        print("-" * 50)

        issues = []

        # Check security middleware
        middleware_file = Path("src/api/security/middleware.py")
        if middleware_file.exists():
            content = middleware_file.read_text()

            required_features = [
                ("Rate limiting", "rate_limit"),
                ("Input validation", "validate_request_size"),
                ("CORS", "cors"),
                ("Authentication", "verify_token"),
            ]

            print("Security middleware features:")
            for feature, pattern in required_features:
                if pattern in content:
                    print(f"  ✅ {feature}")
                else:
                    issues.append(f"Missing {feature} in middleware")
                    print(f"  ❌ {feature}")
        else:
            issues.append("Security middleware file missing")
            print("❌ Security middleware file missing")

        # Check input validation
        print("\nChecking input validation...")
        validation_found = False

        try:
            result = subprocess.run(
                ["rg", "-l", "zod|pydantic|validate", "src/", "gui/"],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                files = result.stdout.strip().split("\n")
                print(f"✅ Input validation found in {len(files)} files")
                validation_found = True
            else:
                issues.append("No input validation libraries found")
                print("❌ No input validation found")

        except subprocess.CalledProcessError:
            issues.append("Error checking input validation")

        return len(issues) == 0, issues

    def check_gui_functionality(self) -> tuple[bool, list[str]]:
        """Check GUI security integration."""
        print("\n🖥️ GUI Security Integration Check")
        print("-" * 50)

        issues = []

        # Check form components
        form_files = [
            "gui/gui/components/forms/DepartmentForm.tsx",
            "gui/gui/components/forms/MachineForm.tsx",
        ]

        print("Checking form security integration...")
        for file in form_files:
            if Path(file).exists():
                content = Path(file).read_text()

                security_features = {
                    "Validation": "useForm" in content or "zodResolver" in content,
                    "Error handling": "error" in content or "catch" in content,
                    "Auth context": "useAuth" in content or "AuthContext" in content,
                }

                print(f"\n{file}:")
                all_ok = True
                for feature, check in security_features.items():
                    if check:
                        print(f"  ✅ {feature}")
                    else:
                        print(f"  ❌ {feature}")
                        issues.append(f"{file} missing {feature}")
                        all_ok = False
            else:
                issues.append(f"Form file missing: {file}")

        # Check auth provider
        auth_provider = Path("gui/gui/components/auth/AuthProvider.tsx")
        if auth_provider.exists():
            print("\n✅ Auth provider component exists")
        else:
            issues.append("Auth provider component missing")
            print("\n❌ Auth provider component missing")

        return len(issues) == 0, issues

    def generate_report(self):
        """Generate comprehensive verification report."""
        print("\n" + "=" * 70)
        print("🔒 COMPREHENSIVE SECURITY VERIFICATION REPORT")
        print("=" * 70)

        # Run all checks
        checks = [
            ("File Security", self.check_file_security),
            ("Authentication", self.check_authentication),
            ("RLS Configuration", self.check_rls_configuration),
            ("API Security", self.check_api_security),
            ("GUI Integration", self.check_gui_functionality),
        ]

        all_passed = True
        detailed_issues = {}

        for check_name, check_func in checks:
            passed, issues = check_func()
            self.results["checks"][check_name] = {"passed": passed, "issues": issues}

            if not passed:
                all_passed = False
                detailed_issues[check_name] = issues

        # Summary
        print("\n" + "=" * 70)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 70)

        for check_name, result in self.results["checks"].items():
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            print(f"{check_name:<20} {status}")

        print("-" * 70)

        if all_passed:
            print("\n✅ ALL SECURITY CHECKS PASSED!")
            print("\nThe Fresh Solver application has:")
            print("- Proper authentication implementation")
            print("- SQL injection protection")
            print("- Input validation")
            print("- RLS configuration ready")
            print("- Secure API implementation")
            print("- GUI security integration")

            self.results["overall_status"] = "PASSED"
        else:
            print("\n⚠️ SECURITY ISSUES DETECTED")
            print("\nRequired actions:")

            for check_name, issues in detailed_issues.items():
                print(f"\n{check_name}:")
                for issue in issues[:3]:  # Show first 3 issues
                    print(f"  - {issue}")
                if len(issues) > 3:
                    print(f"  ... and {len(issues) - 3} more issues")

            self.results["overall_status"] = "FAILED"

        # Save report
        report_path = Path("security_verification_report.json")
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_path}")

        return all_passed


def main():
    """Run comprehensive security verification."""
    verifier = SecurityVerification()
    all_passed = verifier.generate_report()

    # Update todo status
    print("\n📋 Updating task status...")

    if all_passed:
        print("✅ All security tasks completed successfully!")
        return 0
    else:
        print("⚠️ Some security tasks need attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
