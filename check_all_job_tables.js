const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const supabaseUrl = 'https://hnrysjrydbhrnqqkrqir.supabase.co';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkAllJobTables() {
  // Check job_templates
  console.log('=== job_templates table ===');
  const { data: templates } = await supabase.from('job_templates').select('*');
  console.log(`Found ${templates?.length || 0} templates`);
  templates?.forEach(t => console.log(`- ${t.name} (${t.template_id}) - Active: ${t.is_active}`));
  
  // Check job_optimized_patterns (might be the actual table)
  console.log('\n=== job_optimized_patterns table ===');
  const { data: patterns, error } = await supabase.from('job_optimized_patterns').select('*');
  if (error) {
    console.log('Error or table does not exist:', error.message);
  } else {
    console.log(`Found ${patterns?.length || 0} patterns`);
    patterns?.forEach(p => console.log(`- ${p.name} (${p.pattern_id}) - Active: ${p.is_active}`));
  }
  
  // Check job_patterns (another possibility)
  console.log('\n=== job_patterns table ===');
  const { data: jobPatterns, error: jpError } = await supabase.from('job_patterns').select('*');
  if (jpError) {
    console.log('Error or table does not exist:', jpError.message);
  } else {
    console.log(`Found ${jobPatterns?.length || 0} patterns`);
    jobPatterns?.forEach(p => console.log(`- ${p.name}`));
  }
}

checkAllJobTables();