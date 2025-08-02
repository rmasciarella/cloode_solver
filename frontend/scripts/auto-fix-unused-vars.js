#!/usr/bin/env node

/**
 * Auto-fix script for unused variables (TS6133)
 * Prefixes unused parameters with underscore
 */

const fs = require('fs')
const path = require('path')

function fixUnusedVars(filePath, unusedVars) {
  if (!fs.existsSync(filePath)) {
    console.log(`❌ File not found: ${filePath}`)
    return
  }

  let content = fs.readFileSync(filePath, 'utf8')
  let modified = false

  unusedVars.forEach(varName => {
    // Skip if already prefixed with underscore
    if (varName.startsWith('_')) return

    // Pattern 1: Function parameters
    const paramPattern = new RegExp(`(\\(|,\\s*)${varName}(\\s*[,:)])`, 'g')
    if (content.match(paramPattern)) {
      content = content.replace(paramPattern, `$1_${varName}$2`)
      modified = true
      console.log(`  ✓ Fixed parameter: ${varName} → _${varName}`)
      return
    }

    // Pattern 2: Destructured variables
    const destructPattern = new RegExp(`{([^}]*\\b)${varName}(\\b[^}]*)}`, 'g')
    if (content.match(destructPattern)) {
      content = content.replace(destructPattern, `{$1${varName}: _${varName}$2}`)
      modified = true
      console.log(`  ✓ Fixed destructured: ${varName} → _${varName}`)
      return
    }

    // Pattern 3: Regular variable declarations
    const varPattern = new RegExp(`(const|let|var)\\s+${varName}\\b`, 'g')
    if (content.match(varPattern)) {
      content = content.replace(varPattern, `$1 _${varName}`)
      modified = true
      console.log(`  ✓ Fixed variable: ${varName} → _${varName}`)
      return
    }
  })

  if (modified) {
    fs.writeFileSync(filePath, content)
    console.log(`✅ Updated ${path.basename(filePath)}`)
  }
}

// Parse the TypeScript error report
const reportPath = path.join(process.cwd(), 'typescript-error-report.json')
if (!fs.existsSync(reportPath)) {
  console.error('❌ typescript-error-report.json not found. Run fix-typescript-errors.js first.')
  process.exit(1)
}

const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'))

// Group unused variables by file
const unusedByFile = {}
Object.entries(report.files).forEach(([filePath, errors]) => {
  const unusedVars = errors
    .filter(e => e.code === 'TS6133')
    .map(e => {
      const match = e.message.match(/'(\w+)'/)
      return match ? match[1] : null
    })
    .filter(Boolean)
  
  if (unusedVars.length > 0) {
    unusedByFile[filePath] = unusedVars
  }
})

console.log(`🔧 Fixing unused variables in ${Object.keys(unusedByFile).length} files...`)

// Fix each file
Object.entries(unusedByFile).forEach(([filePath, vars]) => {
  console.log(`\n📝 Processing ${path.basename(filePath)}:`)
  fixUnusedVars(filePath, vars)
})

console.log('\n✨ Done! Run TypeScript check again to verify fixes.')