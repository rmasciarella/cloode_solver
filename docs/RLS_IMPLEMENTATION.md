# Row Level Security (RLS) Implementation Guide

## Overview

This document describes the phased implementation of Row Level Security (RLS) for the Fresh Solver OR-Tools constraint programming project. The implementation is designed to add security incrementally without breaking existing GUI functionality.

## Architecture

### Authentication System

- **Frontend**: Next.js with Supabase Auth integration
- **Backend**: Service role authentication for solver operations
- **Fallback**: Development mode bypass for uninterrupted development

### Security Levels

1. **Development Mode**: Authentication can be bypassed
2. **Permissive**: RLS enabled but allows all authenticated operations
3. **Restricted**: Basic role-based access control
4. **Strict**: Full department isolation and role-based restrictions

## Files Structure

```
gui/
├── lib/
│   ├── auth.ts                     # Authentication helpers
│   └── config/security.ts          # Security configuration
├── components/auth/
│   ├── AuthProvider.tsx            # Auth context provider
│   └── AuthGuard.tsx               # Auth protection component
└── .env.development                # Dev environment config

src/
└── data/auth/
    └── service_auth.py             # Backend service authentication

scripts/
├── apply_initial_rls.py            # Apply initial RLS setup
└── security_migration.py          # Gradual security rollout

migrations/
└── 001_initial_rls_setup.sql      # Initial RLS policies
```

## Implementation Phases

### Phase 1: Foundation (Non-Breaking)

**Status**: ✅ Complete

- Add authentication infrastructure with bypass option
- Enable RLS on all tables with permissive policies
- Update services to use authenticated clients
- Maintain existing GUI functionality

**Configuration**:
```bash
NEXT_PUBLIC_DISABLE_AUTH=true
NEXT_PUBLIC_SECURITY_LEVEL=development
```

### Phase 2: Gradual Authentication

**Status**: 🔄 Ready for Testing

- Test authentication in development environment
- Gradually remove auth bypass
- Add user management interface
- Implement basic role structure

**Configuration**:
```bash
NEXT_PUBLIC_DISABLE_AUTH=false
NEXT_PUBLIC_SECURITY_LEVEL=development
```

### Phase 3: Role-Based Access

**Status**: ⏳ Future

- Implement role-based policies
- Add department-based isolation
- Create admin interface for user management
- Enable audit logging

**Configuration**:
```bash
NEXT_PUBLIC_SECURITY_LEVEL=production
NEXT_PUBLIC_RLS_ENFORCEMENT_LEVEL=restricted
```

### Phase 4: Full Security

**Status**: ⏳ Future

- Strict department isolation
- Comprehensive audit logging
- Advanced security features
- Production deployment

**Configuration**:
```bash
NEXT_PUBLIC_SECURITY_LEVEL=production
NEXT_PUBLIC_RLS_ENFORCEMENT_LEVEL=strict
```

## Quick Start

### 1. Apply Initial RLS Setup

```bash
# Apply the initial RLS migration
uv run python scripts/apply_initial_rls.py
```

### 2. Configure Development Environment

```bash
# Copy environment config
cp gui/.env.development gui/.env.local

# Edit gui/.env.local to enable/disable auth
NEXT_PUBLIC_DISABLE_AUTH=true  # Start with bypass enabled
```

### 3. Test GUI Functionality

```bash
# Start GUI with auth bypass
cd gui
npm run dev

# Test all forms work normally
# Authentication should show "Development Mode: Authentication Disabled"
```

### 4. Enable Authentication Testing

```bash
# Edit gui/.env.local
NEXT_PUBLIC_DISABLE_AUTH=false

# Restart GUI - should now show login form
# Use any email/password in development mode
```

### 5. Gradual Security Rollout

```bash
# Apply restricted security level
uv run python scripts/security_migration.py restricted --validate

# Apply strict security level (future)
uv run python scripts/security_migration.py strict --validate
```

## Testing Checklist

### Phase 1 Testing (Current)

- [ ] GUI loads without errors
- [ ] All forms function normally
- [ ] Department form: Create, read, update, delete
- [ ] Machine form: Create, read, update, delete
- [ ] Service operations work (backend solver)
- [ ] Performance monitoring still works
- [ ] No authentication required in dev mode

### Phase 2 Testing (Next)

- [ ] Authentication login/logout works
- [ ] Authenticated users can access all features
- [ ] Service role operations still work
- [ ] Anonymous users cannot access data
- [ ] Session management works correctly

### Phase 3 Testing (Future)

- [ ] Role-based access restrictions work
- [ ] Department isolation functions correctly
- [ ] Admin users can manage other users
- [ ] Audit logging captures all changes
- [ ] Policy violations are properly blocked

## Troubleshooting

### Common Issues

**GUI not loading after RLS setup**:
```bash
# Check RLS policies are permissive
uv run python scripts/security_migration.py permissive
```

**Service operations failing**:
```bash
# Verify service role key is correct
echo $SUPABASE_SERVICE_ROLE_KEY
# Should be a long JWT token starting with "eyJ"
```

**Authentication bypass not working**:
```bash
# Check environment variables
grep DISABLE_AUTH gui/.env.local
grep SECURITY_LEVEL gui/.env.local
```

### Rollback Procedures

**Disable RLS entirely** (emergency):
```sql
-- Connect with service role and run:
ALTER TABLE departments DISABLE ROW LEVEL SECURITY;
ALTER TABLE work_cells DISABLE ROW LEVEL SECURITY;
-- ... repeat for all tables
```

**Reset to permissive policies**:
```bash
uv run python scripts/security_migration.py permissive --validate
```

## Security Configuration Reference

### Environment Variables

| Variable | Values | Description |
|----------|--------|-------------|
| `NEXT_PUBLIC_DISABLE_AUTH` | `true/false` | Bypass authentication in dev |
| `NEXT_PUBLIC_SECURITY_LEVEL` | `development/production` | Overall security mode |
| `NEXT_PUBLIC_RLS_ENFORCEMENT_LEVEL` | `permissive/restricted/strict` | RLS policy level |
| `SUPABASE_SERVICE_ROLE_KEY` | JWT token | Backend service authentication |

### Policy Levels

**Permissive**: Allow all operations for authenticated users
```sql
CREATE POLICY "table_permissive_all" ON table_name
  FOR ALL TO authenticated
  USING (true) WITH CHECK (true);
```

**Restricted**: Basic role-based access
```sql
CREATE POLICY "table_authenticated_read" ON table_name
  FOR SELECT TO authenticated
  USING (true);
```

**Strict**: Department isolation + role-based
```sql
CREATE POLICY "table_department_read" ON table_name
  FOR SELECT TO authenticated
  USING (auth.jwt() ->> 'department_id' = department_id::text);
```

## Migration Commands

```bash
# Apply initial setup
uv run python scripts/apply_initial_rls.py

# Change security level
uv run python scripts/security_migration.py [permissive|restricted|strict]

# Validate current setup
uv run python scripts/security_migration.py [level] --validate

# Target specific tables
uv run python scripts/security_migration.py restricted --tables departments work_cells
```

## Support

For issues with the RLS implementation:

1. Check the troubleshooting section above
2. Verify environment configuration
3. Test with permissive policies first
4. Use service role for backend operations
5. Review Supabase logs for policy violations

## Future Enhancements

- User management interface
- Advanced audit logging
- Integration with external auth providers
- Fine-grained permission system
- Real-time security monitoring