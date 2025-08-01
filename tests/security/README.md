# Comprehensive Security Testing Suite

This directory contains a comprehensive security testing suite for the Fresh Solver project's RLS (Row Level Security) implementation. The test suite ensures that security is properly implemented while preserving GUI functionality and maintaining acceptable performance.

## Overview

The security testing suite validates:

1. **Functionality Preservation** - All existing GUI workflows continue working
2. **Security Validation** - RLS policies properly restrict unauthorized access  
3. **Performance Impact** - Security overhead remains within acceptable limits
4. **Migration Safety** - Rollout procedures are safe and reversible
5. **Configuration Testing** - Different security levels work correctly

## Test Architecture

```
tests/security/
├── README.md                           # This file
├── test_rls_security_implementation.py # Backend RLS security tests
├── test_security_config.py             # Test configuration and utilities
├── test_gui_security_integration.spec.js # GUI security integration tests
└── test_service_security_integration.test.tsx # Service layer security tests

gui/tests/
├── security/
│   └── test_gui_security_integration.spec.js # GUI-specific security tests
└── integration/
    └── test_service_security_integration.test.tsx # Service integration tests

scripts/
└── run_security_tests.py              # Comprehensive test runner
```

## Test Categories

### 1. Backend Security Tests (`test_rls_security_implementation.py`)

**Purpose**: Validate RLS policies, authentication, and backend security enforcement

**Key Test Classes**:
- `TestRLSSecurityImplementation` - Comprehensive RLS validation
- `TestSecurityPerformanceRequirements` - Performance benchmarks

**Test Scenarios**:
- Functionality preservation with security enabled
- Security level enforcement (NONE/OPTIONAL/READ/WRITE/ADMIN)
- Development mode security bypass
- Service role escalation and privilege bypass
- RLS policy enforcement and cross-user access prevention
- Performance impact measurement (< 10% degradation)
- Concurrent security operations
- Migration safety and rollback procedures
- Rate limiting and abuse prevention

**Example Usage**:
```bash
# Run all backend security tests
pytest tests/security/test_rls_security_implementation.py -v

# Run only security performance tests
pytest tests/security/test_rls_security_implementation.py -v -m performance

# Run with detailed output
pytest tests/security/test_rls_security_implementation.py -v --tb=long
```

### 2. GUI Security Integration Tests (`test_gui_security_integration.spec.js`)

**Purpose**: Ensure GUI functionality is preserved while security is properly integrated

**Test Categories**:
- **Functionality Preservation**: All GUI forms work with security enabled
- **Security Context**: Auth state maintained across operations
- **Performance Impact**: Security overhead within acceptable limits
- **Service Layer Integration**: Services work with security context
- **Error Handling**: Security errors handled gracefully
- **Development Mode**: Security bypass works in dev environment
- **Concurrent Operations**: Multiple users with security context
- **Migration Safety**: System works during security rollback

**Example Usage**:
```bash
# Run GUI security tests
npx playwright test tests/security/test_gui_security_integration.spec.js

# Run with browser UI visible
npx playwright test tests/security/test_gui_security_integration.spec.js --headed

# Run specific test
npx playwright test tests/security/test_gui_security_integration.spec.js -g "Functionality Preservation"
```

### 3. Service Layer Security Tests (`test_service_security_integration.test.tsx`)

**Purpose**: Validate security integration at the service layer level

**Test Focus Areas**:
- BaseService security integration (client selection, error handling)
- Department/Machine/Solver service security
- Authentication helper integration
- RLS policy respect in service operations
- Performance tracking for security operations
- Concurrent operations with different users
- Security error recovery and graceful degradation

**Example Usage**:
```bash
# Run service layer security tests
npm test tests/integration/test_service_security_integration.test.tsx

# Run with coverage
npm test tests/integration/test_service_security_integration.test.tsx --coverage

# Run in watch mode
npm test tests/integration/test_service_security_integration.test.tsx --watch
```

## Test Configuration (`test_security_config.py`)

Provides comprehensive configuration and utilities for security testing:

**Key Components**:
- `SecurityTestConfig` - Test configuration settings
- `TestUser` - Test user fixtures with different roles/permissions
- `SecurityTestResult` - Structured test result tracking
- `SecurityTestFixtures` - Standardized test data
- `SecurityTestRunner` - Orchestrates test execution
- `security_test_environment` - Context manager for test setup

**Configuration Options**:
```python
config = SecurityTestConfig(
    enable_auth=True,
    dev_mode_bypass=False,
    max_auth_overhead_ms=100.0,
    max_performance_degradation_percent=10.0,
    enable_rls_policies=True,
    test_migration_safety=True
)
```

## Comprehensive Test Runner (`run_security_tests.py`)

**Purpose**: Execute complete security test suite with reporting

**Usage Options**:
```bash
# Run complete security test suite
python scripts/run_security_tests.py --full

# Run only backend tests
python scripts/run_security_tests.py --backend-only

# Run only GUI tests  
python scripts/run_security_tests.py --gui-only

# Include performance benchmarks
python scripts/run_security_tests.py --performance

# Include migration safety tests
python scripts/run_security_tests.py --migration

# Generate detailed report
python scripts/run_security_tests.py --full --report

# Use custom configuration
python scripts/run_security_tests.py --config custom-config.json

# Specify output location
python scripts/run_security_tests.py --full --output test-results/security-report.json
```

**Output Includes**:
- Test execution summary
- Security compliance status
- Performance benchmark results
- Migration safety validation
- Detailed recommendations
- Next steps for deployment

## Test Patterns

### GIVEN-WHEN-THEN Pattern

All tests follow the GIVEN-WHEN-THEN pattern for clarity:

```python
def test_security_level_enforcement(self):
    """Test: Different security levels are properly enforced.
    
    GIVEN: Security system with multiple security levels
    WHEN: We test operations at each security level  
    THEN: Appropriate access control should be enforced
    """
    # GIVEN: Test requests for each security level
    auth_request = AuthenticatedRequest(...)
    
    # WHEN: Testing authorization
    is_authorized = auth_request.is_authorized_for_level(SecurityLevel.READ)
    
    # THEN: Authorization should match expectations
    assert is_authorized == expected_result
```

### Performance Testing Pattern

Performance tests measure and validate security overhead:

```python
def test_auth_overhead_performance(self):
    # GIVEN: Performance requirements
    max_auth_overhead_ms = 100
    
    # WHEN: Measuring auth overhead
    start_time = time.time()
    # ... perform auth operations ...
    auth_duration = (time.time() - start_time) * 1000
    
    # THEN: Auth overhead should be acceptable
    assert auth_duration < max_auth_overhead_ms
```

## Security Test Users

Standard test users with different security contexts:

```python
test_users = {
    "regular_user": TestUser(
        user_id="user-123",
        role="user", 
        permissions=["read_own_data", "write_own_data"]
    ),
    "admin_user": TestUser(
        user_id="admin-456",
        role="admin",
        permissions=["read_all_data", "admin_operations"]
    ),
    "service_role": TestUser(
        user_id="service-role",
        role="service_role",
        permissions=["bypass_rls", "admin_operations"],
        is_service_role=True
    )
}
```

## Performance Requirements

Security implementation must meet these performance criteria:

- **Authentication Overhead**: < 100ms per request
- **Performance Degradation**: < 10% with security enabled
- **RLS Query Impact**: Minimal query performance impact
- **Concurrent Users**: Support 10+ concurrent authenticated users
- **Rate Limiting**: 60 requests per minute per client

## Security Compliance Validation

Tests validate compliance with security requirements:

1. **Access Control**: Users can only access authorized data
2. **RLS Enforcement**: Row Level Security policies properly restrict access
3. **Service Role Bypass**: Admin operations use service role appropriately
4. **Authentication**: Proper authentication required for protected operations
5. **Authorization**: Correct authorization levels enforced
6. **Graceful Degradation**: System remains functional when security is disabled

## Migration Safety

Migration safety tests ensure:

1. **Rollback Procedures**: Security can be safely disabled/rolled back
2. **Graceful Degradation**: System continues functioning during rollback
3. **Configuration Changes**: Security config changes don't break system
4. **Development Environment**: Dev mode bypass works correctly
5. **Production Readiness**: Security properly enforced in production

## Error Handling

Security error scenarios are tested:

1. **Authentication Failures**: Expired tokens, invalid credentials
2. **Authorization Failures**: Insufficient permissions, policy violations
3. **Rate Limiting**: Request limits exceeded
4. **Service Unavailable**: Auth service temporarily unavailable
5. **Configuration Errors**: Invalid security configuration

## Reporting

Test reports include:

```json
{
  "test_execution": {
    "overall_success": true,
    "duration_seconds": 45.67,
    "successful_categories": 7,
    "total_categories": 7
  },
  "security_compliance": {
    "functionality_preserved": true,
    "security_enforced": true, 
    "performance_acceptable": true,
    "migration_safe": true
  },
  "recommendations": [
    "All security tests passed - ready for production deployment"
  ],
  "next_steps": [
    "Proceed with security rollout to staging environment",
    "Run integration tests in staging environment"
  ]
}
```

## Integration with CI/CD

Add to your CI/CD pipeline:

```yaml
# .github/workflows/security-tests.yml
- name: Run Security Tests
  run: |
    python scripts/run_security_tests.py --full --report
    
- name: Upload Security Report
  uses: actions/upload-artifact@v3
  with:
    name: security-test-report
    path: test-results/security-test-report-*.json
```

## Troubleshooting

### Common Issues

1. **Auth Service Not Available**
   ```bash
   # Check if auth service is running
   curl http://localhost:8000/api/v1/health
   ```

2. **Database Connection Issues**
   ```bash
   # Verify database connection
   python -c "from src.data.loaders.optimized_database import OptimizedDatabaseLoader; loader = OptimizedDatabaseLoader(use_test_tables=True); print(len(loader.load_available_patterns()))"
   ```

3. **GUI Tests Failing**
   ```bash
   # Install dependencies
   cd gui && npm install
   npx playwright install
   ```

4. **Performance Tests Timing Out**
   - Increase timeout values in test configuration
   - Check system resource usage during tests

### Debug Mode

Run tests with debug logging:

```bash
# Backend tests with debug logging
PYTHONPATH=. python -m pytest tests/security/ -v -s --log-cli-level=DEBUG

# GUI tests with debug
DEBUG=1 npx playwright test tests/security/ --headed
```

## Contributing

When adding new security tests:

1. Follow GIVEN-WHEN-THEN patterns
2. Include performance measurements
3. Test both success and failure scenarios
4. Update test documentation
5. Validate with comprehensive test runner

## Security Considerations

- Tests use mock data and test databases only
- No production credentials in test code
- Test users have limited, controlled permissions
- Security test data is cleaned up after tests
- Tests validate security without compromising it