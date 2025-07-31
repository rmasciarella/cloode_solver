// Test data fixtures for consistent testing

const testData = {
  departments: {
    valid: {
      code: 'DEPT_001',
      name: 'Test Department',
      description: 'Department created by automated test'
    },
    minimal: {
      code: 'MIN_DEPT',
      name: 'Minimal Department'
    },
    invalid: {
      code: '', // Empty required field
      name: 'Invalid Department'
    }
  },

  machines: {
    valid: {
      code: 'MACH_001',
      name: 'Test Machine',
      description: 'Machine created by automated test'
    },
    minimal: {
      code: 'MIN_MACH',
      name: 'Minimal Machine'
    }
  },

  workCells: {
    valid: {
      code: 'CELL_001',
      name: 'Test Work Cell',
      description: 'Work cell created by automated test'
    }
  },

  operators: {
    valid: {
      code: 'OP_001',
      name: 'Test Operator',
      email: 'test.operator@example.com'
    }
  },

  jobTemplates: {
    valid: {
      code: 'JOB_TEMPLATE_001',
      name: 'Test Job Template',
      description: 'Job template created by automated test'
    }
  },

  jobInstances: {
    valid: {
      code: 'JOB_INST_001',
      name: 'Test Job Instance',
      quantity: '10',
      due_date: '2024-12-31'
    }
  },

  skills: {
    valid: {
      code: 'SKILL_001',
      name: 'Test Skill',
      description: 'Skill created by automated test'
    }
  }
};

// Navigation structure for testing
const navigationStructure = [
  {
    title: 'Organization',
    items: [
      { key: 'departments', label: 'Departments', hasForm: true, hasTable: true },
      { key: 'work-cells', label: 'Work Cells', hasForm: true, hasTable: true },
      { key: 'business-calendars', label: 'Business Calendars', hasForm: true, hasTable: true }
    ]
  },
  {
    title: 'Templates',
    items: [
      { key: 'job-templates', label: 'Job Templates', hasForm: true, hasTable: true },
      { key: 'template-tasks', label: 'Template Tasks', hasForm: true, hasTable: true }
    ]
  },
  {
    title: 'Resources',
    items: [
      { key: 'machines', label: 'Machines', hasForm: true, hasTable: true },
      { key: 'operators', label: 'Operators', hasForm: true, hasTable: true },
      { key: 'skills', label: 'Skills', hasForm: true, hasTable: true },
      { key: 'sequence-resources', label: 'Sequence Resources', hasForm: true, hasTable: true }
    ]
  },
  {
    title: 'Scheduling',
    items: [
      { key: 'setup-times', label: 'Setup Times', hasForm: true, hasTable: true }
    ]
  },
  {
    title: 'Jobs',
    items: [
      { key: 'job-instances', label: 'Job Instances', hasForm: true, hasTable: true }
    ]
  }
];

// Common selectors for testing
const selectors = {
  navigation: {
    sidebar: 'nav',
    sectionButton: (title) => `button:has-text("${title}")`,
    pageButton: (label) => `button:has-text("${label}")`
  },
  forms: {
    form: 'form',
    submitButton: 'button[type="submit"]',
    codeField: 'input[id="code"]',
    nameField: 'input[id="name"]',
    descriptionField: 'textarea[id="description"]',
    emailField: 'input[id="email"]',
    quantityField: 'input[id="quantity"]',
    dueDateField: 'input[id="due_date"]'
  },
  tables: {
    table: 'table',
    header: 'thead th',
    rows: 'tbody tr',
    cells: 'tbody td'
  },
  feedback: {
    errorElements: '[class*="error"], .text-red-500, .text-red-600',
    successElements: 'text=/success/i',
    toastElements: '[class*="toast"]',
    loadingElements: 'text=/loading/i'
  },
  dropdowns: {
    combobox: '[role="combobox"]',
    option: '[role="option"]',
    select: 'select'
  }
};

// Test helper functions
const helpers = {
  /**
   * Generate unique test code with timestamp
   */
  generateTestCode: (prefix = 'TEST') => {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 5).toUpperCase()}`;
  },

  /**
   * Wait for element to be visible with timeout
   */
  waitForElement: async (page, selector, timeout = 5000) => {
    try {
      await page.waitForSelector(selector, { state: 'visible', timeout });
      return true;
    } catch {
      return false;
    }
  },

  /**
   * Navigate to a specific page section
   */
  navigateToPage: async (page, sectionTitle, pageLabel) => {
    // Expand section
    await page.click(selectors.navigation.sectionButton(sectionTitle));
    await page.waitForTimeout(500);
    
    // Click page
    await page.click(selectors.navigation.pageButton(pageLabel));
    await page.waitForTimeout(1000);
  },

  /**
   * Fill form with test data
   */
  fillForm: async (page, formData) => {
    for (const [fieldId, value] of Object.entries(formData)) {
      const selector = `input[id="${fieldId}"], textarea[id="${fieldId}"], select[id="${fieldId}"]`;
      const element = page.locator(selector);
      
      if (await element.count() > 0) {
        if (await element.getAttribute('type') === 'date') {
          await element.fill(value);
        } else {
          await element.fill(value);
        }
      }
    }
  },

  /**
   * Check for validation errors
   */
  checkValidationErrors: async (page) => {
    const errorCount = await page.locator(selectors.feedback.errorElements).count();
    const errorMessages = [];
    
    if (errorCount > 0) {
      const errorElements = await page.locator(selectors.feedback.errorElements).all();
      for (const element of errorElements) {
        const text = await element.textContent();
        if (text && text.trim()) {
          errorMessages.push(text.trim());
        }
      }
    }
    
    return {
      hasErrors: errorCount > 0,
      errorCount,
      errorMessages
    };
  },

  /**
   * Take screenshot with consistent naming
   */
  takeScreenshot: async (page, name, options = {}) => {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const filename = `test-results/${name}-${timestamp}.png`;
    
    await page.screenshot({ 
      path: filename,
      fullPage: true,
      ...options 
    });
    
    return filename;
  }
};

module.exports = {
  testData,
  navigationStructure,
  selectors,
  helpers
};