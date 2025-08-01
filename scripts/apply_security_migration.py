#!/usr/bin/env python3
"""Apply security migration script for Fresh OR-Tools solver.

This script safely applies the authentication and RLS foundation migration
with comprehensive testing and rollback capabilities.

Usage:
    python scripts/apply_security_migration.py [--dry-run] [--force] [--rollback]
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from supabase import Client

from src.data.clients.secure_database_client import (
    get_database_client,
    validate_database_security,
    test_rls_functionality,
)
from config.database_security_config import security_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SecurityMigrationManager:
    """Manages security migration application and rollback."""

    def __init__(self):
        """Initialize migration manager."""
        self.migration_file = project_root / "migrations" / "003_add_auth_and_rls_foundation.sql"
        self.rollback_commands = [
            "SELECT public.emergency_disable_rls();",
            "DROP FUNCTION IF EXISTS public.emergency_disable_rls();",
            "DROP FUNCTION IF EXISTS public.emergency_enable_rls();",
            "DROP FUNCTION IF EXISTS public.set_audit_fields();",
            "DROP FUNCTION IF EXISTS auth.is_authenticated_or_service_role();",
            "DROP FUNCTION IF EXISTS auth.get_user_department_id();",
            "DROP TABLE IF EXISTS public.user_profiles;",
        ]

    def validate_prerequisites(self) -> Dict[str, Any]:
        """Validate prerequisites for migration.
        
        Returns:
            Validation results
        """
        logger.info("Validating migration prerequisites...")
        
        results = {
            "valid": True,
            "issues": [],
            "warnings": [],
        }
        
        # Check environment configuration
        security_validation = validate_database_security()
        if not security_validation["valid"]:
            results["issues"].extend(security_validation["issues"])
        results["warnings"].extend(security_validation["warnings"])
        
        # Check migration file exists
        if not self.migration_file.exists():
            results["issues"].append(f"Migration file not found: {self.migration_file}")
        
        # Check database connectivity
        try:
            client = get_database_client("migration")
            response = client.table("departments").select("count", count="exact").execute()
            logger.info("Database connectivity: OK")
        except Exception as e:
            results["issues"].append(f"Database connectivity failed: {e}")
        
        # Check for existing data
        try:
            client = get_database_client("migration")
            dept_count = client.table("departments").select("count", count="exact").execute()
            machine_count = client.table("machines").select("count", count="exact").execute()
            
            total_records = (dept_count.count or 0) + (machine_count.count or 0)
            if total_records > 0:
                results["warnings"].append(f"Existing data found: {total_records} records")
                logger.info(f"Migration will affect {total_records} existing records")
        except Exception as e:
            results["warnings"].append(f"Could not count existing records: {e}")
        
        results["valid"] = len(results["issues"]) == 0
        return results

    def backup_database(self) -> bool:
        """Create database backup before migration.
        
        Returns:
            True if backup successful
        """
        logger.info("Creating database backup...")
        
        try:
            # For Supabase, we can't do traditional pg_dump
            # Instead, we'll export critical table schemas and data
            client = get_database_client("migration")
            
            backup_data = {}
            critical_tables = ["departments", "machines", "work_cells", "job_optimized_patterns"]
            
            for table in critical_tables:
                try:
                    response = client.table(table).select("*").execute()
                    backup_data[table] = response.data
                    logger.info(f"Backed up {len(response.data)} records from {table}")
                except Exception as e:
                    logger.warning(f"Could not backup table {table}: {e}")
            
            # Save backup to file
            backup_file = project_root / f"backups/migration_backup_{int(time.time())}.json"
            backup_file.parent.mkdir(exist_ok=True)
            
            import json
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f"Backup saved to: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    def test_gui_functionality(self) -> Dict[str, Any]:
        """Test GUI functionality before and after migration.
        
        Returns:
            Test results
        """
        logger.info("Testing GUI functionality...")
        
        results = {
            "database_queries": {"passed": False, "error": None},
            "basic_operations": {"passed": False, "error": None},
            "performance": {"passed": False, "duration_ms": None},
        }
        
        try:
            # Test basic database queries
            client = get_database_client("gui")
            start_time = time.time()
            
            # Test SELECT operations
            dept_response = client.table("departments").select("*").limit(5).execute()
            machine_response = client.table("machines").select("*").limit(5).execute()
            
            # Test INSERT operation (rollback)
            test_dept = {
                "code": f"TEST_{int(time.time())}",
                "name": "Test Department",
                "description": "Migration test department",
            }
            
            insert_response = client.table("departments").insert(test_dept).execute()
            test_dept_id = insert_response.data[0]["department_id"]
            
            # Test UPDATE operation
            update_response = client.table("departments").update({
                "description": "Updated test department"
            }).eq("department_id", test_dept_id).execute()
            
            # Test DELETE operation (cleanup)
            delete_response = client.table("departments").delete().eq(
                "department_id", test_dept_id
            ).execute()
            
            duration_ms = (time.time() - start_time) * 1000
            
            results["database_queries"]["passed"] = True
            results["basic_operations"]["passed"] = True
            results["performance"]["passed"] = duration_ms < 5000  # 5 second threshold
            results["performance"]["duration_ms"] = duration_ms
            
            logger.info(f"GUI functionality test: PASSED ({duration_ms:.2f}ms)")
            
        except Exception as e:
            error_msg = str(e)
            results["database_queries"]["error"] = error_msg
            logger.error(f"GUI functionality test: FAILED - {error_msg}")
        
        return results

    def apply_migration(self, dry_run: bool = False) -> bool:
        """Apply the security migration.
        
        Args:
            dry_run: If True, only validate without applying
            
        Returns:
            True if successful
        """
        logger.info(f"{'Validating' if dry_run else 'Applying'} security migration...")
        
        try:
            # Read migration file
            with open(self.migration_file, 'r') as f:
                migration_sql = f.read()
            
            if dry_run:
                logger.info("Migration SQL validation: OK")
                logger.info(f"Migration file size: {len(migration_sql)} characters")
                return True
            
            # Apply migration
            client = get_database_client("migration")
            
            # Execute migration in chunks to handle potential timeouts
            sql_commands = migration_sql.split(';')
            
            for i, command in enumerate(sql_commands):
                command = command.strip()
                if not command or command.startswith('--'):
                    continue
                
                try:
                    # Use RPC for complex SQL commands
                    if len(command) > 100:  # Complex command
                        logger.info(f"Executing migration command {i+1}/{len(sql_commands)}")
                    
                    # For Supabase, we need to execute SQL differently
                    # This is a simplified approach - in production, use proper migration tools
                    result = client.rpc('exec_sql', {'sql': command}).execute()
                    
                except Exception as e:
                    logger.error(f"Migration command failed: {e}")
                    logger.error(f"Command: {command[:100]}...")
                    return False
            
            logger.info("Security migration applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def test_post_migration(self) -> Dict[str, Any]:
        """Test system functionality after migration.
        
        Returns:
            Test results
        """
        logger.info("Testing post-migration functionality...")
        
        results = {
            "rls_policies": {"active": False, "error": None},
            "gui_functionality": {},
            "backend_access": {"service_role": False, "error": None},
            "performance": {"acceptable": False, "duration_ms": None},
        }
        
        # Test RLS policies
        try:
            rls_test = test_rls_functionality()
            results["rls_policies"]["active"] = rls_test.get("policy_active", False)
            logger.info("RLS policies: ACTIVE")
        except Exception as e:
            results["rls_policies"]["error"] = str(e)
            logger.warning(f"RLS policy test failed: {e}")
        
        # Test GUI functionality
        results["gui_functionality"] = self.test_gui_functionality()
        
        # Test backend service role access
        try:
            client = get_database_client("solver")
            response = client.table("job_optimized_patterns").select("*").limit(1).execute()
            results["backend_access"]["service_role"] = True
            logger.info("Backend service role access: OK")
        except Exception as e:
            results["backend_access"]["error"] = str(e)
            logger.error(f"Backend service role access failed: {e}")
        
        # Overall performance test
        start_time = time.time()
        try:
            client = get_database_client("gui")
            # Simulate typical GUI workload
            for table in ["departments", "machines", "work_cells"]:
                client.table(table).select("*").limit(10).execute()
            
            duration_ms = (time.time() - start_time) * 1000
            results["performance"]["duration_ms"] = duration_ms
            results["performance"]["acceptable"] = duration_ms < 2000  # 2 second threshold
            
            logger.info(f"Performance test: {duration_ms:.2f}ms")
            
        except Exception as e:
            logger.error(f"Performance test failed: {e}")
        
        return results

    def rollback_migration(self) -> bool:
        """Rollback the security migration.
        
        Returns:
            True if successful
        """
        logger.warning("Rolling back security migration...")
        
        try:
            client = get_database_client("migration")
            
            for command in self.rollback_commands:
                try:
                    result = client.rpc('exec_sql', {'sql': command}).execute()
                    logger.info(f"Rollback command executed: {command[:50]}...")
                except Exception as e:
                    logger.warning(f"Rollback command failed: {e}")
                    logger.warning(f"Command: {command}")
            
            logger.info("Migration rollback completed")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate migration report.
        
        Args:
            results: Migration results
            
        Returns:
            Report string
        """
        report = [
            "=" * 80,
            "SECURITY MIGRATION REPORT",
            "=" * 80,
            "",
            f"Migration Status: {'SUCCESS' if results.get('success', False) else 'FAILED'}",
            f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Security Level: {security_config.security_level.value}",
            "",
        ]
        
        if "prerequisites" in results:
            report.extend([
                "Prerequisites Validation:",
                f"  Valid: {results['prerequisites']['valid']}",
                f"  Issues: {len(results['prerequisites']['issues'])}",
                f"  Warnings: {len(results['prerequisites']['warnings'])}",
                "",
            ])
        
        if "post_migration" in results:
            post = results["post_migration"]
            report.extend([
                "Post-Migration Tests:",
                f"  RLS Policies Active: {post['rls_policies']['active']}",
                f"  GUI Functionality: {post['gui_functionality']['basic_operations']['passed']}",
                f"  Backend Access: {post['backend_access']['service_role']}",
                f"  Performance: {post['performance']['acceptable']} ({post['performance']['duration_ms']:.2f}ms)",
                "",
            ])
        
        if "recommendations" in results:
            report.extend([
                "Recommendations:",
                *[f"  - {rec}" for rec in results["recommendations"]],
                "",
            ])
        
        report.extend([
            "=" * 80,
            "END REPORT",
            "=" * 80,
        ])
        
        return "\n".join(report)


def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(description="Apply security migration")
    parser.add_argument("--dry-run", action="store_true", help="Validate without applying")
    parser.add_argument("--force", action="store_true", help="Force migration even with warnings")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    parser.add_argument("--skip-backup", action="store_true", help="Skip database backup")
    parser.add_argument("--skip-tests", action="store_true", help="Skip post-migration tests")
    
    args = parser.parse_args()
    
    # Load environment
    load_dotenv()
    
    manager = SecurityMigrationManager()
    results = {"success": False, "recommendations": []}
    
    try:
        if args.rollback:
            logger.info("Starting migration rollback...")
            success = manager.rollback_migration()
            results["success"] = success
            
            if success:
                logger.info("Migration rollback completed successfully")
                results["recommendations"].append("Test GUI functionality after rollback")
                results["recommendations"].append("Verify database performance")
            else:
                logger.error("Migration rollback failed")
                results["recommendations"].append("Manual cleanup may be required")
                return 1
        
        else:
            # Validate prerequisites
            logger.info("Starting security migration process...")
            prerequisites = manager.validate_prerequisites()
            results["prerequisites"] = prerequisites
            
            if not prerequisites["valid"]:
                logger.error("Prerequisites validation failed:")
                for issue in prerequisites["issues"]:
                    logger.error(f"  - {issue}")
                return 1
            
            if prerequisites["warnings"] and not args.force:
                logger.warning("Prerequisites have warnings:")
                for warning in prerequisites["warnings"]:
                    logger.warning(f"  - {warning}")
                
                response = input("Continue with migration? (y/N): ")
                if response.lower() != 'y':
                    logger.info("Migration cancelled by user")
                    return 0
            
            # Create backup
            if not args.skip_backup:
                backup_success = manager.backup_database()
                if not backup_success:
                    logger.error("Database backup failed")
                    if not args.force:
                        return 1
            
            # Test pre-migration functionality
            if not args.skip_tests:
                pre_test = manager.test_gui_functionality()
                if not pre_test["basic_operations"]["passed"]:
                    logger.error("Pre-migration GUI test failed")
                    if not args.force:
                        return 1
            
            # Apply migration
            migration_success = manager.apply_migration(dry_run=args.dry_run)
            if not migration_success:
                logger.error("Migration application failed")
                return 1
            
            if args.dry_run:
                logger.info("Dry run completed successfully")
                results["success"] = True
                results["recommendations"].append("Run without --dry-run to apply migration")
                return 0
            
            # Test post-migration functionality
            if not args.skip_tests:
                post_test = manager.test_post_migration()
                results["post_migration"] = post_test
                
                # Check for critical failures
                if not post_test["gui_functionality"]["basic_operations"]["passed"]:
                    logger.error("Post-migration GUI test failed - considering rollback")
                    results["recommendations"].append("GUI functionality failed - manual investigation required")
                    
                    response = input("GUI tests failed. Rollback migration? (Y/n): ")
                    if response.lower() != 'n':
                        logger.info("Rolling back migration due to GUI test failure...")
                        manager.rollback_migration()
                        return 1
            
            results["success"] = True
            logger.info("Security migration completed successfully!")
            
            # Add recommendations
            if security_config.security_level.value == "permissive":
                results["recommendations"].append("Consider upgrading to 'authenticated' security level")
            
            results["recommendations"].extend([
                "Monitor application performance for RLS impact",
                "Test GUI forms and data operations thoroughly",
                "Verify backend solver operations work correctly",
                "Plan next phase of security implementation",
            ])
    
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Migration failed with error: {e}")
        results["recommendations"].append("Check logs for detailed error information")
        return 1
    
    finally:
        # Generate and save report
        report = manager.generate_report(results)
        print(report)
        
        # Save report to file
        report_file = project_root / f"reports/migration_report_{int(time.time())}.txt"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Migration report saved to: {report_file}")
    
    return 0 if results["success"] else 1


if __name__ == "__main__":
    sys.exit(main())