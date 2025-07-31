const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://oggdidyjvncncxgebcpy.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nZ2RpZHlqdm5jbmN4Z2ViY3B5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMyMDQ4MDEsImV4cCI6MjA2ODc4MDgwMX0.7_YyKNm34NPPWs8_IkXJ3yTprEvJIxEpMEMO4s3xudk';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function listAllTables() {
  console.log('📋 Listing all available tables...\n');
  
  try {
    // Get list of all tables using Supabase's RPC or information schema
    const { data, error } = await supabase
      .rpc('list_tables_with_counts')
      .select();
      
    if (error) {
      console.log('📋 Fallback: Trying to list tables by attempting common table names...\n');
      
      const commonTables = [
        'departments', 'business_calendars', 'work_cells', 'machines', 
        'operators', 'skills', 'sequence_resources', 'maintenance_types',
        'job_instances', 'optimized_tasks', 'job_optimized_patterns',
        'template_tasks', 'job_templates', 'template_task_setup_times',
        'task_setup_times', 'optimized_task_setup_times'
      ];
      
      let existingTables = [];
      
      for (const tableName of commonTables) {
        try {
          const { data: testData, error: testError } = await supabase
            .from(tableName)
            .select('*', { count: 'exact', head: true });
            
          if (!testError) {
            existingTables.push({
              table_name: tableName,
              row_count: testData?.length || 0
            });
          }
        } catch (err) {
          // Table doesn't exist, continue
        }
      }
      
      console.log('✅ Existing tables:');
      existingTables.forEach(table => {
        console.log(`   📄 ${table.table_name}`);
      });
      
      console.log(`\n📊 Total tables found: ${existingTables.length}`);
      
    } else {
      console.log('✅ Tables found:');
      data.forEach(table => {
        console.log(`   📄 ${table.table_name} (${table.row_count || 0} rows)`);
      });
    }
    
  } catch (err) {
    console.error('💥 Error listing tables:', err.message);
  }
}

listAllTables();