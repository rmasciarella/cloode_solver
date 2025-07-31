const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Missing Supabase environment variables');
  console.log('NEXT_PUBLIC_SUPABASE_URL:', supabaseUrl ? 'Set' : 'Missing');
  console.log('NEXT_PUBLIC_SUPABASE_ANON_KEY:', supabaseKey ? 'Set' : 'Missing'); 
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkDatabaseTables() {
  console.log('🔍 Checking available database tables...\n');
  
  // Try to get information about available tables
  try {
    console.log('📋 Testing common table names:');
    
    const tables = [
      'departments', 
      'job_templates', 
      'job_optimized_patterns',
      'machines',
      'work_cells',
      'business_calendars',
      'operators',
      'skills',
      'sequence_resources',
      'maintenance_types',
      'job_instances',
      'template_tasks',
      'template_task_setup_times'
    ];
    
    for (const tableName of tables) {
      try {
        const { data, error, count } = await supabase
          .from(tableName)
          .select('*', { count: 'exact', head: true });
          
        if (error) {
          console.log(`❌ ${tableName}: ${error.message}`);
        } else {
          console.log(`✅ ${tableName}: exists (${count || 0} rows)`);
        }
      } catch (err) {
        console.log(`❌ ${tableName}: ${err.message}`);
      }
    }
    
    console.log('\n🔍 Trying to get schema information...');
    
    // Try to query information_schema if available
    try {
      const { data: schemaData, error: schemaError } = await supabase
        .rpc('get_schema_info');
        
      if (schemaError) {
        console.log('ℹ️ Schema RPC not available:', schemaError.message);
      } else {
        console.log('📊 Schema info:', schemaData);
      }
    } catch (err) {
      console.log('ℹ️ Schema query not supported');
    }
    
    // Check if we can access some specific data to confirm working tables
    console.log('\n📊 Checking existing data:');
    
    try {
      const { data: deptData, error: deptError } = await supabase
        .from('departments')
        .select('department_id, name, code')
        .limit(3);
        
      if (!deptError && deptData) {
        console.log('✅ Departments sample:', deptData);
      }
    } catch (err) {
      console.log('ℹ️ Could not fetch departments sample');
    }
    
  } catch (error) {
    console.error('❌ Error checking database:', error);
  }
}

checkDatabaseTables();