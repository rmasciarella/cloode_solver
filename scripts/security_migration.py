#!/usr/bin/env python3
"""
Security migration script for gradual RLS rollout.
Allows progressive tightening of security policies without breaking existing functionality.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from supabase import create_client, Client
from dotenv import load_dotenv

class SecurityLevel(Enum):
    """Security enforcement levels"""
    PERMISSIVE = "permissive"    # Allow all operations (development)
    RESTRICTED = "restricted"    # Basic role-based restrictions
    STRICT = "strict"           # Full security enforcement

@dataclass
class PolicyDefinition:
    """RLS policy definition"""
    table: str
    name: str
    operation: str  # SELECT, INSERT, UPDATE, DELETE, ALL
    to_role: str   # authenticated, anon, specific roles
    using_clause: str
    with_check_clause: Optional[str] = None

class SecurityMigrator:
    """Manages gradual security policy rollout"""
    
    def __init__(self):
        load_dotenv()
        
        url = os.environ.get("SUPABASE_URL")
        service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
        
        self.client = create_client(url, service_key)
        
    def get_current_policies(self, table: str) -> List[Dict]:
        """Get current RLS policies for a table"""
        try:
            result = self.client.rpc('get_table_policies', {'table_name': table})
            return result.data if result.data else []
        except Exception as e:
            print(f"Warning: Could not fetch policies for {table}: {e}")
            return []
    
    def apply_security_level(self, level: SecurityLevel, tables: Optional[List[str]] = None):
        """Apply security policies for the specified level"""
        target_tables = tables or self._get_all_tables()
        
        print(f"Applying {level.value} security level to {len(target_tables)} tables...")
        
        for table in target_tables:
            try:
                self._update_table_policies(table, level)
                print(f"✓ Updated policies for {table}")
            except Exception as e:
                print(f"✗ Failed to update {table}: {e}")
    
    def _get_all_tables(self) -> List[str]:
        """Get list of all tables that need RLS"""
        return [
            'departments',
            'work_cells',
            'machine_resources',
            'job_templates',
            'job_template_tasks',
            'task_dependencies',
            'job_instances',
            'job_instance_tasks',
            'task_assignments',
            'operators',
            'skills',
            'operator_skills',
            'task_skill_requirements',
            'shift_calendars',
            'shift_calendar_periods'
        ]
    
    def _update_table_policies(self, table: str, level: SecurityLevel):
        """Update RLS policies for a table based on security level"""
        # Drop existing policies
        self._drop_table_policies(table)
        
        # Create new policies based on level
        if level == SecurityLevel.PERMISSIVE:
            self._create_permissive_policies(table)
        elif level == SecurityLevel.RESTRICTED:
            self._create_restricted_policies(table)
        elif level == SecurityLevel.STRICT:
            self._create_strict_policies(table)
    
    def _drop_table_policies(self, table: str):
        """Drop all existing policies for a table"""
        policies = self.get_current_policies(table)
        
        for policy in policies:
            policy_name = policy.get('policyname')
            if policy_name:
                try:
                    self.client.rpc('drop_policy', {
                        'table_name': table,
                        'policy_name': policy_name
                    })
                except Exception as e:
                    print(f"Warning: Could not drop policy {policy_name}: {e}")
    
    def _create_permissive_policies(self, table: str):
        """Create permissive policies (development mode)"""
        policies = [
            PolicyDefinition(
                table=table,
                name=f"{table}_permissive_all",
                operation="ALL",
                to_role="authenticated", 
                using_clause="true",
                with_check_clause="true"
            ),
            PolicyDefinition(
                table=table,
                name=f"{table}_public_read",
                operation="SELECT",
                to_role="anon",
                using_clause="true"
            )
        ]
        
        for policy in policies:
            self._create_policy(policy)
    
    def _create_restricted_policies(self, table: str):
        """Create restricted policies (basic role-based access)"""
        policies = [
            PolicyDefinition(
                table=table,
                name=f"{table}_authenticated_read",
                operation="SELECT",
                to_role="authenticated",
                using_clause="true"
            ),
            PolicyDefinition(
                table=table,
                name=f"{table}_authenticated_write",
                operation="INSERT",
                to_role="authenticated",
                using_clause="true",
                with_check_clause="true"
            ),
            PolicyDefinition(
                table=table,
                name=f"{table}_authenticated_update",
                operation="UPDATE", 
                to_role="authenticated",
                using_clause="true",
                with_check_clause="true"
            ),
            PolicyDefinition(
                table=table,
                name=f"{table}_authenticated_delete",
                operation="DELETE",
                to_role="authenticated",
                using_clause="true"
            )
        ]
        
        for policy in policies:
            self._create_policy(policy)
    
    def _create_strict_policies(self, table: str):
        """Create strict policies (full role-based and department isolation)"""
        # Department-based policies (example for future implementation)
        if table in ['departments', 'work_cells', 'machine_resources']:
            policies = [
                PolicyDefinition(
                    table=table,
                    name=f"{table}_department_read",
                    operation="SELECT",
                    to_role="authenticated",
                    using_clause="auth.jwt() ->> 'department_id' = department_id::text OR auth.jwt() ->> 'role' = 'admin'"
                ),
                PolicyDefinition(
                    table=table,
                    name=f"{table}_admin_write",
                    operation="ALL",
                    to_role="authenticated",
                    using_clause="auth.jwt() ->> 'role' = 'admin'",
                    with_check_clause="auth.jwt() ->> 'role' = 'admin'"
                )
            ]
        else:
            # Default strict policies
            policies = [
                PolicyDefinition(
                    table=table,
                    name=f"{table}_authenticated_read",
                    operation="SELECT",
                    to_role="authenticated",
                    using_clause="true"
                ),
                PolicyDefinition(
                    table=table,
                    name=f"{table}_role_based_write",
                    operation="ALL",
                    to_role="authenticated",
                    using_clause="auth.jwt() ->> 'role' IN ('admin', 'manager')",
                    with_check_clause="auth.jwt() ->> 'role' IN ('admin', 'manager')"
                )
            ]
        
        for policy in policies:
            self._create_policy(policy)
    
    def _create_policy(self, policy: PolicyDefinition):
        """Create a single RLS policy"""
        sql = f"""
        CREATE POLICY "{policy.name}" ON {policy.table}
          FOR {policy.operation}
          TO {policy.to_role}
          USING ({policy.using_clause})
        """
        
        if policy.with_check_clause:
            sql += f"\n  WITH CHECK ({policy.with_check_clause})"
        
        try:
            self.client.rpc('execute_sql', {'query': sql})
        except Exception as e:
            raise Exception(f"Failed to create policy {policy.name}: {e}")
    
    def validate_migration(self, tables: Optional[List[str]] = None) -> bool:
        """Validate that the migration was successful"""
        target_tables = tables or self._get_all_tables()
        success = True
        
        print("Validating migration...")
        
        for table in target_tables:
            try:
                # Test basic read access
                result = self.client.table(table).select('*').limit(1).execute()
                print(f"✓ {table}: Read access OK")
            except Exception as e:
                print(f"✗ {table}: Read access failed - {e}")
                success = False
        
        return success

def main():
    """Main migration script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage RLS security migration')
    parser.add_argument('level', choices=['permissive', 'restricted', 'strict'],
                       help='Security level to apply')
    parser.add_argument('--tables', nargs='+', help='Specific tables to migrate')
    parser.add_argument('--validate', action='store_true', help='Validate after migration')
    
    args = parser.parse_args()
    
    migrator = SecurityMigrator()
    level = SecurityLevel(args.level)
    
    # Apply migration
    migrator.apply_security_level(level, args.tables)
    
    # Validate if requested
    if args.validate:
        success = migrator.validate_migration(args.tables)
        if not success:
            print("Migration validation failed!")
            exit(1)
        else:
            print("Migration validation successful!")

if __name__ == "__main__":
    main()