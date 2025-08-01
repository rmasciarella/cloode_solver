-- =============================================================================
-- SIMPLIFIED RLS MIGRATION FOR MANUAL EXECUTION
-- =============================================================================

-- Step 1: Add audit columns to departments
ALTER TABLE departments ADD COLUMN IF NOT EXISTS created_by UUID;
ALTER TABLE departments ADD COLUMN IF NOT EXISTS updated_by UUID;
ALTER TABLE departments ADD COLUMN IF NOT EXISTS tenant_id UUID;

-- Step 2: Add audit columns to machines  
ALTER TABLE machines ADD COLUMN IF NOT EXISTS created_by UUID;
ALTER TABLE machines ADD COLUMN IF NOT EXISTS updated_by UUID;
ALTER TABLE machines ADD COLUMN IF NOT EXISTS tenant_id UUID;

-- Step 3: Add audit columns to work_cells
ALTER TABLE work_cells ADD COLUMN IF NOT EXISTS created_by UUID;
ALTER TABLE work_cells ADD COLUMN IF NOT EXISTS updated_by UUID;
ALTER TABLE work_cells ADD COLUMN IF NOT EXISTS tenant_id UUID;

-- Step 4: Create user profiles table
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'operator', 'manager', 'admin')),
    department_id UUID REFERENCES departments(department_id),
    tenant_id UUID,
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 5: Create RLS function for permissive access (Phase 1)
CREATE OR REPLACE FUNCTION auth.is_authenticated_or_service_role()
RETURNS BOOLEAN AS $$
BEGIN
    -- Service role bypasses all RLS
    IF current_setting('role') = 'service_role' THEN
        RETURN TRUE;
    END IF;
    
    -- PERMISSIVE: Allow all access including anon (Phase 1)
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 6: Enable RLS on core tables
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE machines ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_cells ENABLE ROW LEVEL SECURITY;

-- Step 7: Create permissive policies for departments
DROP POLICY IF EXISTS departments_select_policy ON departments;
CREATE POLICY departments_select_policy ON departments
    FOR SELECT USING (auth.is_authenticated_or_service_role());

DROP POLICY IF EXISTS departments_insert_policy ON departments;
CREATE POLICY departments_insert_policy ON departments
    FOR INSERT WITH CHECK (auth.is_authenticated_or_service_role());

DROP POLICY IF EXISTS departments_update_policy ON departments;
CREATE POLICY departments_update_policy ON departments
    FOR UPDATE USING (auth.is_authenticated_or_service_role());

DROP POLICY IF EXISTS departments_delete_policy ON departments;
CREATE POLICY departments_delete_policy ON departments
    FOR DELETE USING (auth.is_authenticated_or_service_role());

-- Step 8: Create permissive policies for machines
DROP POLICY IF EXISTS machines_select_policy ON machines;
CREATE POLICY machines_select_policy ON machines
    FOR SELECT USING (auth.is_authenticated_or_service_role());

DROP POLICY IF EXISTS machines_insert_policy ON machines;
CREATE POLICY machines_insert_policy ON machines
    FOR INSERT WITH CHECK (auth.is_authenticated_or_service_role());

DROP POLICY IF EXISTS machines_update_policy ON machines;
CREATE POLICY machines_update_policy ON machines
    FOR UPDATE USING (auth.is_authenticated_or_service_role());

DROP POLICY IF EXISTS machines_delete_policy ON machines;
CREATE POLICY machines_delete_policy ON machines
    FOR DELETE USING (auth.is_authenticated_or_service_role());

-- Step 9: Create permissive policies for work_cells
DROP POLICY IF EXISTS work_cells_select_policy ON work_cells;
CREATE POLICY work_cells_select_policy ON work_cells
    FOR SELECT USING (auth.is_authenticated_or_service_role());

DROP POLICY IF EXISTS work_cells_insert_policy ON work_cells;
CREATE POLICY work_cells_insert_policy ON work_cells
    FOR INSERT WITH CHECK (auth.is_authenticated_or_service_role());

DROP POLICY IF EXISTS work_cells_update_policy ON work_cells;
CREATE POLICY work_cells_update_policy ON work_cells
    FOR UPDATE USING (auth.is_authenticated_or_service_role());

DROP POLICY IF EXISTS work_cells_delete_policy ON work_cells;
CREATE POLICY work_cells_delete_policy ON work_cells
    FOR DELETE USING (auth.is_authenticated_or_service_role());

-- Step 10: Create emergency recovery functions
CREATE OR REPLACE FUNCTION public.emergency_disable_rls()
RETURNS TEXT AS $$
BEGIN
    -- Only for development/emergency use
    ALTER TABLE departments DISABLE ROW LEVEL SECURITY;
    ALTER TABLE machines DISABLE ROW LEVEL SECURITY;  
    ALTER TABLE work_cells DISABLE ROW LEVEL SECURITY;
    RETURN 'RLS disabled on core tables';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.emergency_enable_rls()
RETURNS TEXT AS $$
BEGIN
    ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
    ALTER TABLE machines ENABLE ROW LEVEL SECURITY;
    ALTER TABLE work_cells ENABLE ROW LEVEL SECURITY;
    RETURN 'RLS enabled on core tables';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;