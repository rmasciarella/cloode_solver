"""Security configuration management for API endpoints.

Provides centralized configuration for authentication, authorization,
and security policies with environment-based overrides.
"""

import logging
import os
from typing import Dict, Optional

from .auth import AuthConfig, SecurityLevel

logger = logging.getLogger(__name__)


class SecurityConfigManager:
    """Manages security configuration with environment-based overrides."""
    
    def __init__(self):
        self._config: Optional[AuthConfig] = None
        self._endpoint_overrides: Dict[str, SecurityLevel] = {}
    
    def get_config(self) -> AuthConfig:
        """Get current security configuration."""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def reload_config(self) -> AuthConfig:
        """Reload configuration from environment."""
        self._config = self._load_config()
        logger.info("Security configuration reloaded")
        return self._config
    
    def _load_config(self) -> AuthConfig:
        """Load configuration from environment variables."""
        # Parse boolean environment variables
        enabled = self._parse_bool_env("API_SECURITY_ENABLED", False)
        fail_gracefully = self._parse_bool_env("API_SECURITY_FAIL_GRACEFULLY", True)
        allow_service_role = self._parse_bool_env("API_SECURITY_ALLOW_SERVICE_ROLE", True)
        enable_rate_limiting = self._parse_bool_env("API_SECURITY_RATE_LIMITING", True)
        enable_input_validation = self._parse_bool_env("API_SECURITY_INPUT_VALIDATION", True)
        
        # Parse numeric environment variables
        requests_per_minute = self._parse_int_env("API_SECURITY_RATE_LIMIT", 60, 1, 1000)
        max_request_size = self._parse_float_env("API_SECURITY_MAX_REQUEST_MB", 10.0, 0.1, 100.0)
        
        # Parse security level
        default_level_str = os.getenv("API_SECURITY_DEFAULT_LEVEL", "optional").lower()
        default_level = self._parse_security_level(default_level_str, SecurityLevel.OPTIONAL)
        
        config = AuthConfig(
            enabled=enabled,
            default_level=default_level,
            allow_service_role_escalation=allow_service_role,
            fail_gracefully=fail_gracefully,
            enable_rate_limiting=enable_rate_limiting,
            requests_per_minute=requests_per_minute,
            enable_input_validation=enable_input_validation,
            max_request_size_mb=max_request_size,
        )
        
        logger.info(f"Security configuration loaded: enabled={enabled}, level={default_level.value}")
        return config
    
    def get_endpoint_security_level(self, path: str) -> SecurityLevel:
        """Get security level for specific endpoint with overrides."""
        # Check for specific override
        if path in self._endpoint_overrides:
            return self._endpoint_overrides[path]
        
        # Check environment-based overrides
        env_var = f"API_SECURITY_LEVEL_{path.replace('/', '_').replace('-', '_').upper()}"
        level_str = os.getenv(env_var)
        if level_str:
            level = self._parse_security_level(level_str.lower(), None)
            if level:
                self._endpoint_overrides[path] = level
                return level
        
        # Return default level
        return self.get_config().default_level
    
    def set_endpoint_override(self, path: str, level: SecurityLevel) -> None:
        """Set security level override for specific endpoint."""
        self._endpoint_overrides[path] = level
        logger.info(f"Security level override set: {path} -> {level.value}")
    
    def clear_endpoint_overrides(self) -> None:
        """Clear all endpoint security level overrides."""
        self._endpoint_overrides.clear()
        logger.info("All endpoint security overrides cleared")
    
    def get_security_summary(self) -> dict:
        """Get summary of current security configuration."""
        config = self.get_config()
        return {
            "enabled": config.enabled,
            "default_level": config.default_level.value,
            "service_role_escalation": config.allow_service_role_escalation,
            "graceful_degradation": config.fail_gracefully,
            "rate_limiting": {
                "enabled": config.enable_rate_limiting,
                "requests_per_minute": config.requests_per_minute,
            },
            "input_validation": {
                "enabled": config.enable_input_validation,
                "max_request_size_mb": config.max_request_size_mb,
            },
            "endpoint_overrides": {
                path: level.value for path, level in self._endpoint_overrides.items()
            },
        }
    
    @staticmethod
    def _parse_bool_env(var_name: str, default: bool) -> bool:
        """Parse boolean environment variable."""
        value = os.getenv(var_name, "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        else:
            return default
    
    @staticmethod
    def _parse_int_env(var_name: str, default: int, min_val: int, max_val: int) -> int:
        """Parse integer environment variable with bounds checking."""
        try:
            value = int(os.getenv(var_name, str(default)))
            return max(min_val, min(max_val, value))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _parse_float_env(var_name: str, default: float, min_val: float, max_val: float) -> float:
        """Parse float environment variable with bounds checking."""
        try:
            value = float(os.getenv(var_name, str(default)))
            return max(min_val, min(max_val, value))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _parse_security_level(level_str: str, default: Optional[SecurityLevel]) -> Optional[SecurityLevel]:
        """Parse security level from string."""
        level_map = {
            "none": SecurityLevel.NONE,
            "optional": SecurityLevel.OPTIONAL,
            "read": SecurityLevel.READ,
            "write": SecurityLevel.WRITE,
            "admin": SecurityLevel.ADMIN,
        }
        
        return level_map.get(level_str, default)


# Global configuration manager instance
_config_manager: Optional[SecurityConfigManager] = None


def get_security_config_manager() -> SecurityConfigManager:
    """Get the global security configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = SecurityConfigManager()
    return _config_manager


def get_security_config() -> AuthConfig:
    """Get the current security configuration."""
    return get_security_config_manager().get_config()


# Security configuration presets for different environments
SECURITY_PRESETS = {
    "development": AuthConfig(
        enabled=False,
        default_level=SecurityLevel.OPTIONAL,
        allow_service_role_escalation=True,
        fail_gracefully=True,
        enable_rate_limiting=False,
        requests_per_minute=1000,
        enable_input_validation=True,
        max_request_size_mb=50.0,
    ),
    
    "testing": AuthConfig(
        enabled=True,
        default_level=SecurityLevel.OPTIONAL,
        allow_service_role_escalation=True,
        fail_gracefully=True,
        enable_rate_limiting=True,
        requests_per_minute=100,
        enable_input_validation=True,
        max_request_size_mb=10.0,
    ),
    
    "production": AuthConfig(
        enabled=True,
        default_level=SecurityLevel.READ,
        allow_service_role_escalation=True,
        fail_gracefully=False,
        enable_rate_limiting=True,
        requests_per_minute=60,
        enable_input_validation=True,
        max_request_size_mb=10.0,
    ),
}


def load_preset_config(preset_name: str) -> AuthConfig:
    """Load a predefined security configuration preset."""
    if preset_name not in SECURITY_PRESETS:
        raise ValueError(f"Unknown security preset: {preset_name}")
    
    config = SECURITY_PRESETS[preset_name]
    logger.info(f"Loaded security preset: {preset_name}")
    return config