const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// Simple CSV parser
function parseCSV(content) {
  const lines = content.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.trim());
  const data = [];
  
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim());
    const row = {};
    headers.forEach((header, index) => {
      row[header] = values[index] || '';
    });
    data.push(row);
  }
  
  return data;
}

// Helper function to read CSV file
function readCSV(filename) {
  const filePath = path.join(__dirname, '../../supabase_data', filename);
  const fileContent = fs.readFileSync(filePath, 'utf-8');
  return parseCSV(fileContent);
}

// Helper function to wait and retry on failure
async function retryAction(page, action, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await action();
      return;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await page.waitForTimeout(1000);
    }
  }
}

test.describe('Mass Upload Supabase Data', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('https://tiny-tapioca-72f6c6.netlify.app');
    
    // TODO: Login if required
    // For now, we'll assume guest access or you'll need to add login credentials
  });

  test('Upload Work Cells', async ({ page }) => {
    const workCells = readCSV('work_cells.csv');
    
    // Navigate to Work Cells section
    await page.click('a[href="#work-cells"]');
    await page.waitForTimeout(1000);
    
    for (const cell of workCells) {
      console.log(`Creating work cell: ${cell.name}`);
      
      // Click Add/New button (adjust selector as needed)
      await page.click('button:has-text("Add Work Cell"), button:has-text("New Work Cell"), button:has-text("Create Work Cell")');
      
      // Fill form fields - mapping CSV columns to form fields
      // cell_id -> might be auto-generated
      // department -> department field
      if (cell.department) {
        await page.fill('input[name="department"], input[placeholder*="department"]', cell.department);
      }
      
      // name -> name field
      if (cell.name) {
        await page.fill('input[name="name"], input[placeholder*="name"]', cell.name);
      }
      
      // description -> description field
      if (cell.description) {
        await page.fill('textarea[name="description"], textarea[placeholder*="description"]', cell.description);
      }
      
      // capacity -> capacity field
      if (cell.capacity) {
        await page.fill('input[name="capacity"], input[placeholder*="capacity"]', cell.capacity.toString());
      }
      
      // Click save/submit
      await page.click('button:has-text("Save"), button:has-text("Submit"), button:has-text("Create")');
      
      // Wait for success message or navigation
      await page.waitForTimeout(1000);
    }
  });

  test('Upload Skills', async ({ page }) => {
    const skills = readCSV('skills.csv');
    
    // Navigate to Skills section (may need to adjust navigation)
    await page.click('a[href="#skills"], button:has-text("Skills")');
    await page.waitForTimeout(1000);
    
    for (const skill of skills) {
      console.log(`Creating skill: ${skill.name}`);
      
      // Click Add/New button
      await page.click('button:has-text("Add Skill"), button:has-text("New Skill"), button:has-text("Create Skill")');
      
      // Map CSV fields to form fields
      if (skill.name) {
        await page.fill('input[name="name"], input[placeholder*="name"]', skill.name);
      }
      
      if (skill.description) {
        await page.fill('textarea[name="description"], textarea[placeholder*="description"]', skill.description);
      }
      
      // Submit form
      await page.click('button:has-text("Save"), button:has-text("Submit"), button:has-text("Create")');
      await page.waitForTimeout(1000);
    }
  });

  test('Upload Resources/Machines', async ({ page }) => {
    const resources = readCSV('resources.csv');
    
    // Navigate to Machines section
    await page.click('a[href="#machines"]');
    await page.waitForTimeout(1000);
    
    for (const resource of resources) {
      console.log(`Creating machine: ${resource.name}`);
      
      // Click Add/New button
      await page.click('button:has-text("Add Machine"), button:has-text("New Machine"), button:has-text("Create Machine")');
      
      // Map fields - resources.csv has different fields than typical machine form
      // resource_id -> auto-generated
      // cell_id -> work cell (may need to select from dropdown)
      // department -> department field
      // name -> name/machine name
      // type -> machine type
      // capacity -> capacity
      // cost_per_hour -> hourly cost
      
      if (resource.name) {
        await page.fill('input[name="name"], input[name="machineName"], input[placeholder*="name"]', resource.name);
      }
      
      if (resource.department) {
        // May need to select from dropdown
        const deptSelector = 'select[name="department"], input[name="department"]';
        const deptElement = await page.$(deptSelector);
        if (deptElement) {
          await page.selectOption(deptSelector, resource.department);
        } else {
          await page.fill('input[placeholder*="department"]', resource.department);
        }
      }
      
      if (resource.type) {
        await page.fill('input[name="type"], input[placeholder*="type"]', resource.type);
      }
      
      if (resource.capacity) {
        await page.fill('input[name="capacity"], input[placeholder*="capacity"]', resource.capacity.toString());
      }
      
      if (resource.cost_per_hour) {
        await page.fill('input[name="costPerHour"], input[name="cost_per_hour"], input[placeholder*="cost"]', resource.cost_per_hour.toString());
      }
      
      // Submit
      await page.click('button:has-text("Save"), button:has-text("Submit"), button:has-text("Create")');
      await page.waitForTimeout(1000);
    }
  });

  test('Upload Tasks', async ({ page }) => {
    const tasks = readCSV('tasks.csv').slice(0, 5); // Start with just 5 for testing
    
    // Tasks might be under Job Templates or a separate section
    // You'll need to adjust navigation based on actual UI
    await page.click('a[href="#job-templates"]');
    await page.waitForTimeout(1000);
    
    for (const task of tasks) {
      console.log(`Creating task: ${task.name || task.task_id}`);
      
      // This will need to be adjusted based on actual UI structure
      await page.click('button:has-text("Add Task"), button:has-text("New Task")');
      
      // Map CSV fields to form fields
      // task_id, job_id, name, description, earliest_start, latest_finish,
      // setup_time, run_time_per_unit, min_batch_size, max_batch_size, etc.
      
      if (task.name) {
        await page.fill('input[name="name"], input[placeholder*="name"]', task.name);
      }
      
      if (task.description) {
        await page.fill('textarea[name="description"]', task.description);
      }
      
      if (task.setup_time) {
        await page.fill('input[name="setupTime"], input[placeholder*="setup"]', task.setup_time.toString());
      }
      
      if (task.run_time_per_unit) {
        await page.fill('input[name="runTimePerUnit"], input[placeholder*="run time"]', task.run_time_per_unit.toString());
      }
      
      // Submit
      await page.click('button:has-text("Save"), button:has-text("Submit")');
      await page.waitForTimeout(1000);
    }
  });

  test('Upload Holiday Calendar', async ({ page }) => {
    const holidays = readCSV('holiday_calendar.csv');
    
    // Holiday calendar might be under settings or business calendar
    // Adjust navigation as needed
    console.log('Uploading holidays - navigation may need adjustment');
    
    for (const holiday of holidays) {
      console.log(`Creating holiday: ${holiday.name} on ${holiday.holiday_date}`);
      // Implementation depends on where holiday calendar is in the UI
    }
  });
});

// Run specific test with more detailed output
test.describe.configure({ mode: 'serial' }); // Run tests in sequence