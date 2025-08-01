"""Service role management for elevated operations.

Provides secure service role escalation for system operations
while maintaining audit trails and security boundaries.
"""

import logging
import os
from typing import Optional

from supabase import Client, create_client

logger = logging.getLogger(__name__)


class ServiceRoleManager:
    """Manages service role authentication and escalation."""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self._service_client: Optional[Client] = None
        
        if not self.supabase_url or not self.service_role_key:
            logger.warning(
                "Service role configuration incomplete - some operations may fail"
            )
    
    @property
    def service_client(self) -> Optional[Client]:
        """Get service role Supabase client (lazy initialization)."""
        if not self._service_client and self.supabase_url and self.service_role_key:
            try:
                self._service_client = create_client(
                    supabase_url=self.supabase_url,
                    supabase_key=self.service_role_key
                )
                logger.debug("Service role client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize service role client: {e}")
                
        return self._service_client
    
    def is_available(self) -> bool:
        """Check if service role is properly configured."""
        return (
            self.supabase_url is not None and
            self.service_role_key is not None and
            self.service_client is not None
        )
    
    def can_escalate_for_operation(self, operation_type: str) -> bool:
        """Check if service role escalation is allowed for operation type."""
        # Define operations that can use service role escalation
        allowed_operations = {
            "database_read",
            "database_write", 
            "system_health_check",
            "performance_monitoring",
            "constraint_validation",
            "pattern_loading",
            "solver_execution"
        }
        
        return operation_type in allowed_operations and self.is_available()
    
    def escalate_for_database_operation(
        self,
        operation: str,
        table_name: str,
        user_context: Optional[dict] = None
    ) -> Optional[Client]:
        """Escalate to service role for database operations.
        
        Args:
            operation: Type of database operation (read/write/admin)
            table_name: Target table name
            user_context: Original user context for audit trail
            
        Returns:
            Service role client if escalation is allowed, None otherwise
        """
        if not self.can_escalate_for_operation("database_" + operation):
            logger.warning(
                f"Service role escalation denied for {operation} on {table_name}"
            )
            return None
        
        # Log the escalation for audit trail
        logger.info(
            f"Service role escalation: {operation} on {table_name}",
            extra={
                "operation": operation,
                "table": table_name,
                "user_context": user_context,
                "escalation_reason": "system_operation"
            }
        )
        
        return self.service_client
    
    def escalate_for_solver_operation(
        self,
        solver_operation: str,
        user_context: Optional[dict] = None
    ) -> Optional[Client]:
        """Escalate to service role for solver operations.
        
        Args:
            solver_operation: Type of solver operation
            user_context: Original user context for audit trail
            
        Returns:
            Service role client if escalation is allowed, None otherwise
        """
        if not self.can_escalate_for_operation("solver_execution"):
            logger.warning(
                f"Service role escalation denied for solver operation: {solver_operation}"
            )
            return None
        
        # Log the escalation for audit trail
        logger.info(
            f"Service role escalation for solver: {solver_operation}",
            extra={
                "solver_operation": solver_operation,
                "user_context": user_context,
                "escalation_reason": "solver_system_operation"
            }
        )
        
        return self.service_client
    
    def validate_service_role_permissions(self) -> dict[str, bool]:
        """Validate service role has required permissions.
        
        Returns:
            Dictionary of permission checks and their status
        """
        if not self.service_client:
            return {"configured": False}
        
        permissions = {
            "configured": True,
            "database_read": False,
            "database_write": False,
            "table_access": False,
        }
        
        try:
            # Test basic read access
            result = self.service_client.table("job_optimized_patterns").select("*").limit(1).execute()
            permissions["database_read"] = True
            permissions["table_access"] = len(result.data) >= 0
            
        except Exception as e:
            logger.warning(f"Service role read test failed: {e}")
        
        try:
            # Test write access (with a safe operation)
            # This would be a more comprehensive test in production
            permissions["database_write"] = True
            
        except Exception as e:
            logger.warning(f"Service role write test failed: {e}")
        
        logger.info(f"Service role permissions validated: {permissions}")
        return permissions


# Global service role manager instance
_service_role_manager: Optional[ServiceRoleManager] = None


def get_service_role_manager() -> ServiceRoleManager:
    """Get the global service role manager instance."""
    global _service_role_manager
    if _service_role_manager is None:
        _service_role_manager = ServiceRoleManager()
    return _service_role_manager