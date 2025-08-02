const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// Simple CSV parser that handles quoted fields
function parseCSV(content) {
  const lines = content.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
  const data = [];
  
  for (let i = 1; i < lines.length; i++) {
    // Handle potential commas within quoted fields
    const row = {};
    const values = lines[i].match(/(".*?"|[^,]+)(?=\s*,|\s*$)/g) || [];
    
    headers.forEach((header, index) => {
      const value = values[index] ? values[index].trim().replace(/^"|"$/g, '') : '';
      row[header] = value;
    });
    
    // Skip empty rows
    if (Object.values(row).some(v => v)) {
      data.push(row);
    }
  }
  
  return data;
}

// Helper function to read CSV file
function readCSV(filename) {
  const filePath = path.join(__dirname, '../../supabase_data', filename);
  const fileContent = fs.readFileSync(filePath, 'utf-8');
  // Remove BOM if present
  const cleanContent = fileContent.replace(/^\uFEFF/, '');
  return parseCSV(cleanContent);
}

test.describe('Mass Upload Supabase Data', () => {
  // Login before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('https://tiny-tapioca-72f6c6.netlify.app');
    
    // Login with provided credentials
    await page.fill('input[placeholder*="Email"]', 'rmasciarella@acrlabs.io');
    await page.fill('input[type="password"]', 'Inmemory!2020');
    await page.click('button:has-text("Sign In")');
    
    // Wait for navigation to complete
    await page.waitForTimeout(2000);
    
    // Verify we're logged in by checking for sidebar elements
    await expect(page.locator('text=Fresh Solver')).toBeVisible();
  });

  test('1. Upload Work Cells', async ({ page }) => {
    const workCells = readCSV('work_cells.csv');
    console.log(`Found ${workCells.length} work cells to upload`);
    
    // Navigate to Work Cells
    await page.click('button:has-text("Organization")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Work Cells")');
    await page.waitForTimeout(1000);
    
    for (const cell of workCells) {
      console.log(`Creating work cell: ${cell.name}`);
      
      // Click Create/Add button
      await page.click('button:has-text("Create"), button:has-text("Add Work Cell"), button:has-text("New")');
      await page.waitForTimeout(500);
      
      // Fill form based on CSV mapping
      // Work cell form typically has: name, department, capacity, description
      
      if (cell.name) {
        await page.fill('input[name="name"], input[placeholder*="name"]', cell.name);
      }
      
      if (cell.department) {
        // Department might be a select dropdown
        const deptSelect = await page.$('select[name="department_id"], select[name="departmentId"]');
        if (deptSelect) {
          // Try to find option by text
          await page.selectOption('select[name="department_id"], select[name="departmentId"]', { label: cell.department });
        } else {
          await page.fill('input[name="department"], input[placeholder*="department"]', cell.department);
        }
      }
      
      if (cell.capacity) {
        await page.fill('input[name="capacity"], input[placeholder*="capacity"], input[type="number"][placeholder*="capacity"]', cell.capacity.toString());
      }
      
      if (cell.description) {
        await page.fill('textarea[name="description"], textarea[placeholder*="description"]', cell.description);
      }
      
      // Submit form
      await page.click('button[type="submit"], button:has-text("Save"), button:has-text("Create Work Cell")');
      
      // Wait for success or handle errors
      await page.waitForTimeout(1000);
      
      // Check for success message or close modal if needed
      const closeButton = await page.$('button[aria-label="Close"], button:has-text("×")');
      if (closeButton) {
        await closeButton.click();
      }
    }
  });

  test('2. Upload Skills', async ({ page }) => {
    const skills = readCSV('skills.csv');
    console.log(`Found ${skills.length} skills to upload`);
    
    // Navigate to Skills
    await page.click('button:has-text("Resources")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Skills")');
    await page.waitForTimeout(1000);
    
    for (const skill of skills) {
      console.log(`Creating skill: ${skill.name}`);
      
      await page.click('button:has-text("Create"), button:has-text("Add Skill"), button:has-text("New")');
      await page.waitForTimeout(500);
      
      if (skill.name) {
        await page.fill('input[name="name"], input[placeholder*="skill name"]', skill.name);
      }
      
      if (skill.description) {
        await page.fill('textarea[name="description"], textarea[placeholder*="description"]', skill.description);
      }
      
      await page.click('button[type="submit"], button:has-text("Save"), button:has-text("Create Skill")');
      await page.waitForTimeout(1000);
    }
  });

  test('3. Upload Machines/Resources', async ({ page }) => {
    const resources = readCSV('resources.csv');
    console.log(`Found ${resources.length} machines to upload`);
    
    // Navigate to Machines
    await page.click('button:has-text("Resources")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Machines")');
    await page.waitForTimeout(1000);
    
    for (const resource of resources.slice(0, 5)) { // Test with first 5
      console.log(`Creating machine: ${resource.name}`);
      
      await page.click('button:has-text("Create"), button:has-text("Add Machine"), button:has-text("New")');
      await page.waitForTimeout(500);
      
      // Map resource fields to machine form
      if (resource.name) {
        await page.fill('input[name="name"], input[name="machine_name"], input[placeholder*="machine name"]', resource.name);
      }
      
      // Machine code might be derived from name
      const machineCode = resource.name ? resource.name.toUpperCase().replace(/[^A-Z0-9]/g, '') : '';
      await page.fill('input[name="code"], input[name="machine_code"], input[placeholder*="code"]', machineCode);
      
      if (resource.department) {
        const deptSelect = await page.$('select[name="department_id"], select[name="departmentId"]');
        if (deptSelect) {
          try {
            await page.selectOption('select[name="department_id"], select[name="departmentId"]', { label: resource.department });
          } catch {
            // If exact match fails, try first option
            const options = await page.$$eval('select[name="department_id"] option, select[name="departmentId"] option', 
              opts => opts.map(opt => ({ value: opt.value, text: opt.textContent })));
            if (options.length > 1) {
              await page.selectOption('select[name="department_id"], select[name="departmentId"]', options[1].value);
            }
          }
        }
      }
      
      if (resource.capacity) {
        await page.fill('input[name="capacity"], input[placeholder*="capacity"]', resource.capacity.toString());
      }
      
      if (resource.cost_per_hour) {
        await page.fill('input[name="hourly_cost"], input[name="cost_per_hour"], input[placeholder*="cost"]', resource.cost_per_hour.toString());
      }
      
      // Set work cell if needed
      if (resource.cell_id) {
        const cellSelect = await page.$('select[name="work_cell_id"], select[name="workCellId"]');
        if (cellSelect) {
          const options = await page.$$eval('select[name="work_cell_id"] option, select[name="workCellId"] option', 
            opts => opts.map(opt => ({ value: opt.value, text: opt.textContent })));
          if (options.length > 1) {
            await page.selectOption('select[name="work_cell_id"], select[name="workCellId"]', options[1].value);
          }
        }
      }
      
      await page.click('button[type="submit"], button:has-text("Save"), button:has-text("Create Machine")');
      await page.waitForTimeout(1500);
    }
  });

  test('4. Upload Holiday Calendar', async ({ page }) => {
    const holidays = readCSV('holiday_calendar.csv').slice(0, 3); // Test with first 3
    console.log(`Found ${holidays.length} holidays to upload`);
    
    // Navigate to Business Calendars
    await page.click('button:has-text("Organization")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Business Calendars")');
    await page.waitForTimeout(1000);
    
    for (const holiday of holidays) {
      console.log(`Creating holiday: ${holiday.name} on ${holiday.holiday_date}`);
      
      await page.click('button:has-text("Create"), button:has-text("Add Holiday"), button:has-text("New")');
      await page.waitForTimeout(500);
      
      if (holiday.name) {
        await page.fill('input[name="name"], input[placeholder*="holiday name"]', holiday.name);
      }
      
      if (holiday.holiday_date) {
        // Date input might need specific format
        const date = new Date(holiday.holiday_date);
        const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD format
        await page.fill('input[type="date"], input[name="date"], input[placeholder*="date"]', dateStr);
      }
      
      await page.click('button[type="submit"], button:has-text("Save"), button:has-text("Create")');
      await page.waitForTimeout(1000);
    }
  });

  test('5. Upload Job Templates and Tasks', async ({ page }) => {
    const tasks = readCSV('tasks.csv');
    const jobs = readCSV('jobs.csv');
    
    console.log(`Found ${jobs.length} jobs and ${tasks.length} tasks`);
    
    // First, create job templates
    await page.click('button:has-text("Templates")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Job Templates")');
    await page.waitForTimeout(1000);
    
    // Group tasks by job_id to create templates
    const jobGroups = {};
    tasks.forEach(task => {
      if (!jobGroups[task.job_id]) {
        jobGroups[task.job_id] = [];
      }
      jobGroups[task.job_id].push(task);
    });
    
    // Create first job template as example
    const firstJobId = Object.keys(jobGroups)[0];
    if (firstJobId) {
      const job = jobs.find(j => j.job_id === firstJobId);
      console.log(`Creating job template: ${job?.description || firstJobId}`);
      
      await page.click('button:has-text("Create"), button:has-text("Add Template"), button:has-text("New")');
      await page.waitForTimeout(500);
      
      const templateName = job?.description || `Template-${firstJobId.slice(0, 8)}`;
      await page.fill('input[name="name"], input[placeholder*="template name"]', templateName);
      await page.fill('input[name="code"], input[placeholder*="code"]', templateName.replace(/[^A-Z0-9]/gi, '').toUpperCase());
      
      if (job?.description) {
        await page.fill('textarea[name="description"], textarea[placeholder*="description"]', job.description);
      }
      
      await page.click('button[type="submit"], button:has-text("Save"), button:has-text("Create")');
      await page.waitForTimeout(1500);
    }
  });

  // Add more tests for other data types as needed
});

test.describe.configure({ mode: 'serial' }); // Run tests in sequence