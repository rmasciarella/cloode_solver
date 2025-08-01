-- =============================================================================
-- AUTHENTICATION AND RLS FOUNDATION SCHEMA
-- =============================================================================
-- 
-- CRITICAL IMPLEMENTATION STRATEGY:
-- 1. Start with PERMISSIVE policies that preserve existing functionality
-- 2. Add authentication tables without breaking current GUI operations
-- 3. Allow anon access initially, then gradually restrict
-- 4. Service role MUST bypass RLS for system operations
-- 5. Performance impact must be minimal
--
-- =============================================================================

-- =============================================================================
-- 1. AUTHENTICATION TABLES
-- =============================================================================

-- Simple users table for authentication context
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    encrypted_password TEXT,
    email_confirmed_at TIMESTAMPTZ,
    invited_at TIMESTAMPTZ,
    confirmation_token TEXT,
    confirmation_sent_at TIMESTAMPTZ,
    recovery_token TEXT,
    recovery_sent_at TIMESTAMPTZ,
    email_change_token_new TEXT,
    email_change TEXT,
    email_change_sent_at TIMESTAMPTZ,
    email_change_token_current TEXT DEFAULT '',
    email_change_confirm_status SMALLINT DEFAULT 0,
    banned_until TIMESTAMPTZ,
    raw_app_meta_data JSONB,
    raw_user_meta_data JSONB,
    is_super_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    phone TEXT UNIQUE,
    phone_confirmed_at TIMESTAMPTZ,
    phone_change TEXT DEFAULT '',
    phone_change_token TEXT DEFAULT '',
    phone_change_sent_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ GENERATED ALWAYS AS (LEAST(email_confirmed_at, phone_confirmed_at)) STORED,
    email_change_token_current_old TEXT DEFAULT '',
    email_change_confirm_status_old SMALLINT DEFAULT 0,
    is_sso_user BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    is_anonymous BOOLEAN NOT NULL DEFAULT FALSE
);

-- Application-level user profiles extending auth.users
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT,
    first_name TEXT,
    last_name TEXT,
    avatar_url TEXT,
    department_id UUID REFERENCES departments(department_id),
    role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'manager', 'operator', 'user', 'guest')),
    permissions JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    last_seen_at TIMESTAMPTZ,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Session management for tracking active sessions
CREATE TABLE IF NOT EXISTS auth.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    factor_id UUID,
    aal auth.aal_level,
    not_after TIMESTAMPTZ,
    refreshed_at TIMESTAMPTZ,
    user_agent TEXT,
    ip INET,
    tag TEXT
);

-- =============================================================================
-- 2. INDEXES FOR AUTHENTICATION PERFORMANCE
-- =============================================================================

-- Critical indexes for auth performance
CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth.users(email);
CREATE INDEX IF NOT EXISTS idx_auth_users_phone ON auth.users(phone);
CREATE INDEX IF NOT EXISTS idx_auth_users_confirmation_token ON auth.users(confirmation_token);
CREATE INDEX IF NOT EXISTS idx_auth_users_recovery_token ON auth.users(recovery_token);
CREATE INDEX IF NOT EXISTS idx_auth_users_email_change_token_current ON auth.users(email_change_token_current);
CREATE INDEX IF NOT EXISTS idx_auth_users_email_change_token_new ON auth.users(email_change_token_new);
CREATE INDEX IF NOT EXISTS idx_auth_users_is_anonymous ON auth.users(is_anonymous);

-- User profiles indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_department_id ON public.user_profiles(department_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_role ON public.user_profiles(role);
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_active ON public.user_profiles(is_active);

-- Session indexes for RLS performance
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_not_after ON auth.sessions(not_after);

-- =============================================================================
-- 3. RLS-OPTIMIZED INDEXES (CRITICAL FOR PERFORMANCE)
-- =============================================================================

-- Add user tracking columns to core tables (nullable for backward compatibility)
ALTER TABLE departments ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES auth.users(id);
ALTER TABLE departments ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES auth.users(id);
ALTER TABLE departments ADD COLUMN IF NOT EXISTS tenant_id UUID; -- For multi-tenancy

ALTER TABLE machines ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES auth.users(id);
ALTER TABLE machines ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES auth.users(id);
ALTER TABLE machines ADD COLUMN IF NOT EXISTS tenant_id UUID;

ALTER TABLE job_optimized_patterns ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES auth.users(id);
ALTER TABLE job_optimized_patterns ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES auth.users(id);
ALTER TABLE job_optimized_patterns ADD COLUMN IF NOT EXISTS tenant_id UUID;

ALTER TABLE job_instances ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES auth.users(id);
ALTER TABLE job_instances ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES auth.users(id);
ALTER TABLE job_instances ADD COLUMN IF NOT EXISTS tenant_id UUID;

-- RLS performance indexes (CRITICAL)
CREATE INDEX IF NOT EXISTS idx_departments_created_by ON departments(created_by);
CREATE INDEX IF NOT EXISTS idx_departments_tenant_id ON departments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_machines_created_by ON machines(created_by);
CREATE INDEX IF NOT EXISTS idx_machines_tenant_id ON machines(tenant_id);
CREATE INDEX IF NOT EXISTS idx_job_patterns_created_by ON job_optimized_patterns(created_by);
CREATE INDEX IF NOT EXISTS idx_job_patterns_tenant_id ON job_optimized_patterns(tenant_id);
CREATE INDEX IF NOT EXISTS idx_job_instances_created_by ON job_instances(created_by);
CREATE INDEX IF NOT EXISTS idx_job_instances_tenant_id ON job_instances(tenant_id);

-- =============================================================================
-- 4. PERMISSIVE RLS POLICIES (PHASE 1: PRESERVE FUNCTIONALITY)
-- =============================================================================

-- CRITICAL: Start with permissive policies to preserve GUI functionality
-- These can be gradually restricted as authentication is implemented

-- Function to check if user is authenticated or using service role
CREATE OR REPLACE FUNCTION auth.is_authenticated_or_service_role()
RETURNS BOOLEAN AS $$
BEGIN
    -- Service role bypasses all RLS
    IF current_setting('role') = 'service_role' THEN
        RETURN TRUE;
    END IF;
    
    -- Check if user is authenticated
    IF auth.uid() IS NOT NULL THEN
        RETURN TRUE;
    END IF;
    
    -- PERMISSIVE: Allow anon access during migration
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current user's department (for future restriction)
CREATE OR REPLACE FUNCTION auth.get_user_department_id()
RETURNS UUID AS $$
DECLARE
    dept_id UUID;
BEGIN
    -- Service role has access to all departments
    IF current_setting('role') = 'service_role' THEN
        RETURN NULL; -- NULL means access to all
    END IF;
    
    -- Get user's department
    SELECT department_id INTO dept_id
    FROM public.user_profiles
    WHERE id = auth.uid();
    
    RETURN dept_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enable RLS on core tables
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.machines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.work_cells ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_optimized_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.optimized_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.optimized_task_modes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_instances ENABLE ROW LEVEL SECURITY;

-- PERMISSIVE POLICIES (Phase 1): Allow all operations for authenticated users and service role
CREATE POLICY "departments_select_policy" ON public.departments
    FOR SELECT USING (auth.is_authenticated_or_service_role());

CREATE POLICY "departments_insert_policy" ON public.departments
    FOR INSERT WITH CHECK (auth.is_authenticated_or_service_role());

CREATE POLICY "departments_update_policy" ON public.departments
    FOR UPDATE USING (auth.is_authenticated_or_service_role());

CREATE POLICY "departments_delete_policy" ON public.departments
    FOR DELETE USING (auth.is_authenticated_or_service_role());

-- Machines policies
CREATE POLICY "machines_select_policy" ON public.machines
    FOR SELECT USING (auth.is_authenticated_or_service_role());

CREATE POLICY "machines_insert_policy" ON public.machines
    FOR INSERT WITH CHECK (auth.is_authenticated_or_service_role());

CREATE POLICY "machines_update_policy" ON public.machines
    FOR UPDATE USING (auth.is_authenticated_or_service_role());

CREATE POLICY "machines_delete_policy" ON public.machines
    FOR DELETE USING (auth.is_authenticated_or_service_role());

-- Work cells policies
CREATE POLICY "work_cells_select_policy" ON public.work_cells
    FOR SELECT USING (auth.is_authenticated_or_service_role());

CREATE POLICY "work_cells_insert_policy" ON public.work_cells
    FOR INSERT WITH CHECK (auth.is_authenticated_or_service_role());

CREATE POLICY "work_cells_update_policy" ON public.work_cells
    FOR UPDATE USING (auth.is_authenticated_or_service_role());

CREATE POLICY "work_cells_delete_policy" ON public.work_cells
    FOR DELETE USING (auth.is_authenticated_or_service_role());

-- Job patterns policies
CREATE POLICY "job_patterns_select_policy" ON public.job_optimized_patterns
    FOR SELECT USING (auth.is_authenticated_or_service_role());

CREATE POLICY "job_patterns_insert_policy" ON public.job_optimized_patterns
    FOR INSERT WITH CHECK (auth.is_authenticated_or_service_role());

CREATE POLICY "job_patterns_update_policy" ON public.job_optimized_patterns
    FOR UPDATE USING (auth.is_authenticated_or_service_role());

CREATE POLICY "job_patterns_delete_policy" ON public.job_optimized_patterns
    FOR DELETE USING (auth.is_authenticated_or_service_role());

-- Optimized tasks policies
CREATE POLICY "optimized_tasks_select_policy" ON public.optimized_tasks
    FOR SELECT USING (auth.is_authenticated_or_service_role());

CREATE POLICY "optimized_tasks_insert_policy" ON public.optimized_tasks
    FOR INSERT WITH CHECK (auth.is_authenticated_or_service_role());

CREATE POLICY "optimized_tasks_update_policy" ON public.optimized_tasks
    FOR UPDATE USING (auth.is_authenticated_or_service_role());

CREATE POLICY "optimized_tasks_delete_policy" ON public.optimized_tasks
    FOR DELETE USING (auth.is_authenticated_or_service_role());

-- Optimized task modes policies
CREATE POLICY "optimized_task_modes_select_policy" ON public.optimized_task_modes
    FOR SELECT USING (auth.is_authenticated_or_service_role());

CREATE POLICY "optimized_task_modes_insert_policy" ON public.optimized_task_modes
    FOR INSERT WITH CHECK (auth.is_authenticated_or_service_role());

CREATE POLICY "optimized_task_modes_update_policy" ON public.optimized_task_modes
    FOR UPDATE USING (auth.is_authenticated_or_service_role());

CREATE POLICY "optimized_task_modes_delete_policy" ON public.optimized_task_modes
    FOR DELETE USING (auth.is_authenticated_or_service_role());

-- Job instances policies
CREATE POLICY "job_instances_select_policy" ON public.job_instances
    FOR SELECT USING (auth.is_authenticated_or_service_role());

CREATE POLICY "job_instances_insert_policy" ON public.job_instances
    FOR INSERT WITH CHECK (auth.is_authenticated_or_service_role());

CREATE POLICY "job_instances_update_policy" ON public.job_instances
    FOR UPDATE USING (auth.is_authenticated_or_service_role());

CREATE POLICY "job_instances_delete_policy" ON public.job_instances
    FOR DELETE USING (auth.is_authenticated_or_service_role());

-- =============================================================================
-- 5. USER PROFILE POLICIES
-- =============================================================================

-- User profiles RLS
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can view their own profile and admins can view all
CREATE POLICY "user_profiles_select_policy" ON public.user_profiles
    FOR SELECT USING (
        auth.uid() = id OR 
        EXISTS (
            SELECT 1 FROM public.user_profiles up 
            WHERE up.id = auth.uid() AND up.role = 'admin'
        ) OR
        current_setting('role') = 'service_role'
    );

-- Users can update their own profile, admins can update any
CREATE POLICY "user_profiles_update_policy" ON public.user_profiles
    FOR UPDATE USING (
        auth.uid() = id OR 
        EXISTS (
            SELECT 1 FROM public.user_profiles up 
            WHERE up.id = auth.uid() AND up.role = 'admin'
        ) OR
        current_setting('role') = 'service_role'
    );

-- Only admins and service role can insert profiles
CREATE POLICY "user_profiles_insert_policy" ON public.user_profiles
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_profiles up 
            WHERE up.id = auth.uid() AND up.role = 'admin'
        ) OR
        current_setting('role') = 'service_role'
    );

-- =============================================================================
-- 6. AUDIT TRIGGERS FOR SECURITY TRACKING
-- =============================================================================

-- Function to set audit fields
CREATE OR REPLACE FUNCTION public.set_audit_fields()
RETURNS TRIGGER AS $$
BEGIN
    -- Set created_by and updated_by based on current user
    IF TG_OP = 'INSERT' THEN
        NEW.created_by = auth.uid();
        NEW.updated_by = auth.uid();
        NEW.created_at = NOW();
        NEW.updated_at = NOW();
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        NEW.updated_by = auth.uid();
        NEW.updated_at = NOW();
        NEW.created_by = OLD.created_by; -- Preserve original creator
        NEW.created_at = OLD.created_at; -- Preserve original creation time
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add audit triggers to core tables
DROP TRIGGER IF EXISTS departments_audit_trigger ON public.departments;
CREATE TRIGGER departments_audit_trigger
    BEFORE INSERT OR UPDATE ON public.departments
    FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();

DROP TRIGGER IF EXISTS machines_audit_trigger ON public.machines;
CREATE TRIGGER machines_audit_trigger
    BEFORE INSERT OR UPDATE ON public.machines
    FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();

DROP TRIGGER IF EXISTS job_patterns_audit_trigger ON public.job_optimized_patterns;
CREATE TRIGGER job_patterns_audit_trigger
    BEFORE INSERT OR UPDATE ON public.job_optimized_patterns
    FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();

DROP TRIGGER IF EXISTS job_instances_audit_trigger ON public.job_instances;
CREATE TRIGGER job_instances_audit_trigger
    BEFORE INSERT OR UPDATE ON public.job_instances
    FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();

-- =============================================================================
-- 7. CONFIGURATION AND MIGRATION FUNCTIONS
-- =============================================================================

-- Function to disable RLS for emergency recovery
CREATE OR REPLACE FUNCTION admin.disable_rls_emergency()
RETURNS TEXT AS $$
BEGIN
    -- Only superuser can call this
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles 
        WHERE rolname = current_user AND rolsuper = true
    ) THEN
        RAISE EXCEPTION 'Only superuser can disable RLS';
    END IF;
    
    ALTER TABLE public.departments DISABLE ROW LEVEL SECURITY;
    ALTER TABLE public.machines DISABLE ROW LEVEL SECURITY;
    ALTER TABLE public.work_cells DISABLE ROW LEVEL SECURITY;
    ALTER TABLE public.job_optimized_patterns DISABLE ROW LEVEL SECURITY;
    ALTER TABLE public.optimized_tasks DISABLE ROW LEVEL SECURITY;
    ALTER TABLE public.optimized_task_modes DISABLE ROW LEVEL SECURITY;
    ALTER TABLE public.job_instances DISABLE ROW LEVEL SECURITY;
    ALTER TABLE public.user_profiles DISABLE ROW LEVEL SECURITY;
    
    RETURN 'RLS disabled on all tables for emergency recovery';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to re-enable RLS after recovery
CREATE OR REPLACE FUNCTION admin.enable_rls_after_recovery()
RETURNS TEXT AS $$
BEGIN
    -- Only superuser can call this
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles 
        WHERE rolname = current_user AND rolsuper = true
    ) THEN
        RAISE EXCEPTION 'Only superuser can enable RLS';
    END IF;
    
    ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.machines ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.work_cells ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.job_optimized_patterns ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.optimized_tasks ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.optimized_task_modes ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.job_instances ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
    
    RETURN 'RLS enabled on all tables after recovery';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- 8. COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE auth.users IS 'Core authentication users table with Supabase compatibility';
COMMENT ON TABLE public.user_profiles IS 'Application-level user profiles extending auth.users';
COMMENT ON TABLE auth.sessions IS 'Session management for tracking active user sessions';

COMMENT ON FUNCTION auth.is_authenticated_or_service_role() IS 'PERMISSIVE: Allows anon access during migration phase';
COMMENT ON FUNCTION auth.get_user_department_id() IS 'Returns user department for future row-level filtering';
COMMENT ON FUNCTION public.set_audit_fields() IS 'Automatically sets created_by, updated_by, and timestamp fields';
COMMENT ON FUNCTION admin.disable_rls_emergency() IS 'Emergency function to disable RLS - superuser only';
COMMENT ON FUNCTION admin.enable_rls_after_recovery() IS 'Re-enable RLS after emergency recovery - superuser only';

-- =============================================================================
-- 9. INITIAL DATA SETUP
-- =============================================================================

-- Create default admin user profile placeholder (will be populated by application)
-- This is just a placeholder structure - actual user creation happens through Supabase Auth

-- Grant necessary permissions to anon and authenticated roles
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;

-- Service role gets full access (bypasses RLS)
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- =============================================================================
-- IMPLEMENTATION COMPLETE
-- =============================================================================

-- This schema provides:
-- 1. ✅ Authentication foundation without breaking existing functionality
-- 2. ✅ Permissive RLS policies that allow current GUI operations
-- 3. ✅ Service role bypass for system operations
-- 4. ✅ Performance-optimized indexes for RLS
-- 5. ✅ Audit tracking for security
-- 6. ✅ Emergency recovery functions
-- 7. ✅ Gradual migration path from anon to authenticated access
--
-- Next steps:
-- 1. Apply this schema to Supabase
-- 2. Test GUI functionality (should work unchanged)
-- 3. Gradually restrict policies as authentication is implemented
-- 4. Add department-based access controls when ready