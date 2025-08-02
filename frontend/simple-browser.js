const { chromium } = require('playwright');

async function openBrowser() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    await page.goto('https://tiny-tapioca-72f6c6.netlify.app');
    
    console.log('Browser opened. You can manually navigate and upload files.');
    console.log('Available files for upload:');
    console.log('- /Users/quanta/projects/fresh_solver/frontend/template_precedences_corrected.csv (Template Precedences)');
    console.log('- Will create jobs_corrected.csv for you now...');
    
    // Keep browser open
    await new Promise(() => {}); // Never resolves, keeps browser open
}

openBrowser();