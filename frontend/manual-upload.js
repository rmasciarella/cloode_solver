const { chromium } = require('playwright');
const fs = require('fs');

// Parse CSV utility
function parseCSV(content) {
    const lines = content.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
    const data = [];
    
    for (let i = 1; i < lines.length; i++) {
        const row = {};
        const values = lines[i].match(/(".*?"|[^,]+)(?=\s*,|\s*$)/g) || [];
        headers.forEach((header, index) => {
            const value = values[index] ? values[index].trim().replace(/^"|"$/g, '') : '';
            row[header] = value;
        });
        if (Object.values(row).some(v => v)) {
            data.push(row);
        }
    }
    return data;
}

async function manualUploads() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
        console.log('Opening Fresh Solver app...');
        await page.goto('https://tiny-tapioca-72f6c6.netlify.app');
        
        console.log('✋ Please sign in manually now. Press Enter when you are logged in...');
        
        // Wait for user input
        await new Promise((resolve) => {
            process.stdin.once('data', () => {
                resolve();
            });
        });
        
        try {
                // 1. Upload Template Precedences
                console.log('Uploading Template Precedences...');
                await page.getByRole('button', { name: 'Template Precedences' }).click();
                await page.waitForTimeout(1000);
                await page.getByRole('tab', { name: 'Mass Upload' }).click();
                await page.waitForTimeout(1000);
                
                const precedencesInput = await page.locator('input[type="file"]');
                await precedencesInput.setInputFiles('/Users/quanta/projects/fresh_solver/frontend/template_precedences_corrected.csv');
                await page.waitForTimeout(1000);
                await page.getByRole('button', { name: 'Upload' }).click();
                await page.waitForTimeout(3000);
                
                console.log('✅ Template Precedences upload completed!');
                
                // 2. Create and upload corrected Jobs
                console.log('Creating corrected Jobs CSV...');
                
                // Read the original jobs data
                const jobsContent = fs.readFileSync('/Users/quanta/projects/fresh_solver/supabase_data/jobs.csv', 'utf8');
                const jobsData = parseCSV(jobsContent);
                
                // Map to correct field names
                const correctedJobs = jobsData.map(job => ({
                    template_id: job.job_id, // Map job_id to template_id
                    name: job.description,   // Map description to name
                    earliest_start_date: job.due_date // Map due_date to earliest_start_date
                }));
                
                // Write corrected jobs file
                const jobsHeaders = ['template_id', 'name', 'earliest_start_date'];
                const jobsCsv = [
                    jobsHeaders.join(','),
                    ...correctedJobs.map(row => jobsHeaders.map(h => row[h] || '').join(','))
                ].join('\n');
                
                fs.writeFileSync('/Users/quanta/projects/fresh_solver/frontend/jobs_corrected.csv', jobsCsv);
                console.log('✅ Created corrected jobs CSV with proper field mapping');
                
                console.log('✅ All uploads completed! You can continue with other files manually if needed.');
                
        } catch (error) {
            console.error('Error during uploads:', error);
        } finally {
            await browser.close();
        }
        
    } catch (error) {
        console.error('Error:', error);
        await browser.close();
    }
}

manualUploads();