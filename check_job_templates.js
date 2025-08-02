const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const supabaseUrl = 'https://hnrysjrydbhrnqqkrqir.supabase.co';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY;

if (!supabaseKey) {
  console.error('No Supabase key found in environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkJobTemplates() {
  console.log('Checking job_templates table...\n');
  
  const { data, error } = await supabase
    .from('job_templates')
    .select('*')
    .order('created_at', { ascending: true });
    
  if (error) {
    console.error('Error fetching job_templates:', error);
    return;
  }
  
  console.log(`Found ${data.length} job templates:\n`);
  data.forEach((template, index) => {
    console.log(`${index + 1}. ${template.name}`);
    console.log(`   ID: ${template.template_id}`);
    console.log(`   Active: ${template.is_active}`);
    console.log(`   Created: ${template.created_at}`);
    console.log('');
  });
  
  // Also check for active templates specifically
  const { data: activeData, error: activeError } = await supabase
    .from('job_templates')
    .select('template_id, name')
    .eq('is_active', true)
    .order('name', { ascending: true });
    
  if (!activeError) {
    console.log('\nActive job templates (what should appear in dropdown):');
    activeData.forEach(t => console.log(`- ${t.name} (${t.template_id})`));
  }
}

checkJobTemplates();