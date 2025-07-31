# GUI Testing with Playwright

This document explains how to run and maintain the Playwright tests for the Fresh Solver GUI application.

## Setup

The Playwright testing framework is already configured and ready to use. All dependencies are installed via the existing `package.json`.

## Test Structure

The test suite is organized into the following categories:

### Test Files

- **`tests/navigation.spec.js`** - Tests navigation between different sections and pages
- **`tests/forms.spec.js`** - Tests form interactions, validation, and submission
- **`tests/database.spec.js`** - Tests database connectivity and data loading
- **`tests/accessibility.spec.js`** - Tests accessibility features and compliance
- **`tests/comprehensive.spec.js`** - Comprehensive end-to-end test suite

### Supporting Files

- **`tests/fixtures/test-data.js`** - Test data, selectors, and helper functions
- **`playwright.config.js`** - Playwright configuration file

## Running Tests

### Prerequisites

1. Make sure your GUI application is running:
   ```bash
   npm run dev
   ```
   The app should be accessible at `http://localhost:3000`

2. Ensure your database (Supabase) is connected and accessible

### Test Commands

```bash
# Run all tests (headless mode)
npm test

# Run tests with visible browser
npm run test:headed

# Run tests with interactive UI
npm run test:ui

# Run tests in debug mode
npm run test:debug

# Show test report after running
npm run test:report

# Run legacy comprehensive test (your original file)
npm run test:legacy
```

### Running Specific Tests

```bash
# Run only navigation tests
npx playwright test navigation

# Run only form tests
npx playwright test forms

# Run only database tests
npx playwright test database

# Run only accessibility tests
npx playwright test accessibility

# Run comprehensive test suite
npx playwright test comprehensive
```

## Test Results

### Screenshots

Tests automatically capture screenshots in the following scenarios:
- Successful page navigation
- Form interactions
- Error states
- Before and after form submissions

Screenshots are saved in the `test-results/` directory.

### Reports

After running tests, you can view detailed reports:

```bash
npm run test:report
```

This opens an HTML report showing:
- Test results and status
- Screenshots and videos
- Performance metrics
- Error details

## Test Configuration

The tests are configured to:

- **Run against multiple browsers**: Chrome, Firefox, Safari
- **Test mobile viewports**: Pixel 5, iPhone 12
- **Automatically start/stop dev server**: The tests will start your Next.js app if it's not running
- **Capture failures**: Screenshots and videos are automatically saved for failed tests
- **Retry failed tests**: Tests retry up to 2 times on CI

## Writing New Tests

### Basic Test Structure

```javascript
const { test, expect } = require('@playwright/test');
const { helpers, selectors, testData } = require('./fixtures/test-data');

test.describe('My Test Suite', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should do something', async ({ page }) => {
    // Your test code here
    await helpers.navigateToPage(page, 'Organization', 'Departments');
    
    // Take screenshot
    await helpers.takeScreenshot(page, 'my-test');
    
    // Assert something
    await expect(page.locator('h2')).toBeVisible();
  });
});
```

### Using Test Helpers

The `test-data.js` file provides helpful utilities:

```javascript
// Navigate to a page
await helpers.navigateToPage(page, 'Resources', 'Machines');

// Fill form with test data
await helpers.fillForm(page, testData.machines.valid);

// Check for validation errors
const errorCheck = await helpers.checkValidationErrors(page);

// Take consistent screenshots
await helpers.takeScreenshot(page, 'form-filled');

// Generate unique test data
const testCode = helpers.generateTestCode('DEPT');
```

## Debugging Tests

### Debug Mode

Run tests in debug mode to step through them:

```bash
npm run test:debug
```

This will:
- Open a browser in headed mode
- Pause execution at the start of each test
- Allow you to step through line by line
- Show the Playwright Inspector

### Console Logging

Tests automatically log:
- Console errors from the browser
- Network request failures
- Form validation results
- Navigation success/failure

### Screenshots and Videos

Failed tests automatically capture:
- Screenshot at the point of failure
- Video recording of the entire test
- Network request logs
- Console message logs

## Continuous Integration

The tests are configured to work in CI environments:

- **Headless mode**: Tests run without visible browser
- **Retry logic**: Failed tests retry automatically
- **Parallel execution**: Tests run in parallel for speed
- **Artifact collection**: Screenshots and videos are saved as CI artifacts

## Common Issues and Solutions

### Test Timeouts

If tests timeout:
1. Increase the timeout in `playwright.config.js`
2. Add `await page.waitForTimeout(1000)` after navigation
3. Use specific waiters: `await page.waitForSelector('table')`

### Database Connection Issues

If database tests fail:
1. Check Supabase connection in your app
2. Verify environment variables are set
3. Ensure test data exists in the database

### Form Validation Not Working

If form validation tests fail:
1. Check that required field validation is implemented
2. Verify error messages are displayed with correct CSS classes
3. Update selectors in `test-data.js` if needed

### Navigation Issues

If navigation tests fail:
1. Check that all navigation items exist in the sidebar
2. Verify section expand/collapse functionality
3. Update navigation structure in `test-data.js`

## Performance Considerations

The test suite is designed to be:
- **Fast**: Most tests complete in under 30 seconds
- **Reliable**: Tests wait for elements and handle async operations properly
- **Comprehensive**: Cover all major functionality without being redundant

### Optimizing Test Speed

- Tests run in parallel by default
- Screenshots are only taken when needed
- Database operations are minimized
- Network requests are monitored, not mocked

## Maintenance

### Updating Test Data

When adding new forms or fields:
1. Update `testData` in `fixtures/test-data.js`
2. Add new selectors to the `selectors` object
3. Update `navigationStructure` if navigation changes

### Adding New Test Categories

1. Create a new `.spec.js` file in the `tests/` directory
2. Follow the existing patterns for structure and naming
3. Use the helpers and fixtures for consistency
4. Document any new patterns in this README

## Legacy Tests

Your original comprehensive test (`comprehensive_gui_test.js`) is still available:

```bash
npm run test:legacy
```

This runs your original standalone test script, which can be useful for:
- Quick manual verification
- Generating screenshots for documentation
- Testing specific edge cases

The new Playwright test suite provides better structure, reporting, and CI integration, but both approaches can coexist.