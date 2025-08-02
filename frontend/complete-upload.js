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

async function completeUploads() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
        console.log('Starting upload completion...');
        
        // Navigate to deployed Netlify app
        await page.goto('https://tiny-tapioca-72f6c6.netlify.app');
        
        // Wait for page to load and take screenshot to debug
        await page.waitForTimeout(3000);
        await page.screenshot({ path: 'debug-login.png' });
        
        // Click the Sign In button in the banner to open login dialog
        console.log('Clicking Sign In button in banner...');
        await page.getByRole('banner').getByRole('button', { name: 'Sign In' }).click();
        await page.waitForTimeout(1000);
        await page.locator('#email').fill('rmasciarella@acrlabs.io');
        await page.locator('#password').fill('Inmemory!2020');
        await page.getByRole('main').getByRole('button', { name: 'Sign In' }).click();
        await page.waitForTimeout(3000);
        
        // 1. Upload Jobs data
        console.log('Uploading Jobs data...');
        await page.getByRole('button', { name: 'Job Instances' }).click();
        await page.waitForTimeout(1000);
        await page.getByRole('tab', { name: 'Mass Upload' }).click();
        await page.waitForTimeout(1000);
        
        const jobsInput = await page.locator('input[type="file"]');
        await jobsInput.setInputFiles('/Users/quanta/projects/fresh_solver/supabase_data/jobs.csv');
        await page.waitForTimeout(1000);
        await page.getByRole('button', { name: 'Upload' }).click();
        await page.waitForTimeout(3000);
        
        // 2. Upload corrected Template Precedences
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
        
        // 3. Fix and upload Resources
        console.log('Fixing and uploading Resources...');
        
        // First get work cell UUIDs
        await page.getByRole('button', { name: 'Work Cells' }).click();
        await page.waitForTimeout(1000);
        
        // Extract work cell mappings from the UI
        const workCells = await page.evaluate(() => {
            const rows = document.querySelectorAll('table tbody tr');
            const cells = {};
            rows.forEach(row => {
                const nameCell = row.querySelector('td:first-child');
                const idAttr = row.getAttribute('data-id') || row.querySelector('[data-id]')?.getAttribute('data-id');
                if (nameCell && idAttr) {
                    cells[nameCell.textContent.trim()] = idAttr;
                }
            });
            return cells;
        });
        
        console.log('Work cell mappings:', workCells);
        
        // Create corrected resources CSV
        const resourcesContent = fs.readFileSync('/Users/quanta/projects/fresh_solver/supabase_data/resources.csv', 'utf8');
        const resourcesData = parseCSV(resourcesContent);
        
        // Map resource cell_ids to actual work cell UUIDs
        const correctedResources = resourcesData.map(resource => {
            // Try to find matching work cell UUID
            const cellName = resource.cell_id; // This might be a name, not UUID
            const actualCellId = workCells[cellName] || resource.cell_id;
            
            return {
                ...resource,
                cell_id: actualCellId
            };
        });
        
        // Write corrected resources file
        const resourcesHeaders = Object.keys(correctedResources[0]);
        const resourcesCsv = [
            resourcesHeaders.join(','),
            ...correctedResources.map(row => resourcesHeaders.map(h => row[h]).join(','))
        ].join('\n');
        
        fs.writeFileSync('/Users/quanta/projects/fresh_solver/frontend/resources_corrected.csv', resourcesCsv);
        
        // Upload corrected resources
        await page.getByRole('button', { name: 'Machines' }).click();
        await page.waitForTimeout(1000);
        await page.getByRole('tab', { name: 'Mass Upload' }).click();
        await page.waitForTimeout(1000);
        
        const resourcesInput = await page.locator('input[type="file"]');
        await resourcesInput.setInputFiles('/Users/quanta/projects/fresh_solver/frontend/resources_corrected.csv');
        await page.waitForTimeout(1000);
        await page.getByRole('button', { name: 'Upload' }).click();
        await page.waitForTimeout(3000);
        
        console.log('All uploads completed!');
        
    } catch (error) {
        console.error('Error during uploads:', error);
    } finally {
        await browser.close();
    }
}

completeUploads();