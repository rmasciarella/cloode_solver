const { createClient } = require('@supabase/supabase-js');

// These should be set in your environment
const supabaseUrl = 'https://oggdidyjvncncxgebcpy.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nZ2RpZHlqdm5jbmN4Z2ViY3B5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMyMDQ4MDEsImV4cCI6MjA2ODc4MDgwMX0.7_YyKNm34NPPWs8_IkXJ3yTprEvJIxEpMEMO4s3xudk';

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('❌ Missing Supabase environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function testDatabaseFixes() {
  console.log('🔧 Testing database fixes...\n');

  const tests = [
    {
      name: '🎯 FIXED: SetupTimeForm fetchSetupTimes - optimized_task_modes',
      query: () => supabase
        .from('optimized_task_modes')
        .select('*')
        .limit(10)
    },
    {
      name: '🎯 FIXED: SetupTimeForm fetchTemplateTasks - optimized_tasks with job_optimized_patterns',
      query: () => supabase
        .from('optimized_tasks')
        .select(`
          optimized_task_id,
          name,
          pattern_id,
          job_optimized_patterns!inner(name)
        `)
        .order('name', { ascending: true })
        .limit(5)
    },
    {
      name: '🎯 FIXED: SetupTimeForm fetchMachines - machines table',
      query: () => supabase
        .from('machines')
        .select('machine_resource_id, name')
        .eq('is_active', true)
        .order('name', { ascending: true })
        .limit(5)
    }
  ];

  let passedTests = 0;
  let totalTests = tests.length;

  for (const test of tests) {
    try {
      const { data, error } = await test.query();
      
      if (error) {
        console.error(`❌ ${test.name}: ${error.message}`);
        if (error.details) {
          console.error(`   Details: ${error.details}`);
        }
        if (error.hint) {
          console.error(`   Hint: ${error.hint}`);
        }
      } else {
        console.log(`✅ ${test.name}: Found ${data?.length || 0} records`);
        passedTests++;
      }
    } catch (err) {
      console.error(`❌ ${test.name}: ${err.message}`);
    }
  }

  console.log(`\n📊 Results: ${passedTests}/${totalTests} tests passed`);
  
  if (passedTests === totalTests) {
    console.log('🎉 All database fixes are working correctly!');
  } else {
    console.log('⚠️  Some issues remain - check the errors above');
  }
}

testDatabaseFixes().catch((err) => {
  console.error('💥 Test failed:', err.message);
  process.exit(1);
});