const { chromium } = require('playwright');

async function autoUpload() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
        console.log('Navigating to Fresh Solver...');
        await page.goto('https://tiny-tapioca-72f6c6.netlify.app');
        await page.waitForTimeout(3000);
        
        console.log('Clicking Sign In button...');
        await page.click('button:has-text("Sign In")');
        await page.waitForTimeout(2000);
        
        console.log('Filling credentials...');
        await page.fill('input[placeholder*="email" i]', 'rmasciarella@acrlabs.io');
        await page.fill('input[placeholder*="password" i]', 'Inmemory!2020');
        
        console.log('Submitting login...');
        await page.click('button[type="submit"]:has-text("Sign In")');
        await page.waitForTimeout(5000);
        
        console.log('Uploading Template Precedences...');
        await page.click('button:has-text("Template Precedences")');
        await page.waitForTimeout(2000);
        await page.click('button[role="tab"]:has-text("Mass Upload")');
        await page.waitForTimeout(2000);
        
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles('/Users/quanta/projects/fresh_solver/frontend/template_precedences_corrected.csv');
        await page.waitForTimeout(1000);
        await page.click('button:has-text("Upload")');
        await page.waitForTimeout(5000);
        
        console.log('✅ Template Precedences uploaded successfully!');
        
        console.log('Upload completed! Browser will stay open for you to verify.');
        
        // Keep browser open indefinitely so you can see what happened
        await new Promise(() => {});
        
    } catch (error) {
        console.error('Error:', error);
        await page.screenshot({ path: 'error-screenshot.png' });
        // Keep browser open even on error
        await new Promise(() => {});
    }
}

autoUpload();