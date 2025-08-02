#!/usr/bin/env node

/**
 * Auto-fix script for optional property issues (TS2375)
 * Fixes exactOptionalPropertyTypes compliance
 */

const fs = require('fs')
const path = require('path')

function fixOptionalProps(filePath) {
  if (!fs.existsSync(filePath)) {
    console.log(`❌ File not found: ${filePath}`)
    return
  }

  let content = fs.readFileSync(filePath, 'utf8')
  let modified = false

  // Pattern 1: Fix optional properties in interfaces/types
  // Change "property?: type" to "property?: type | undefined"
  const optionalPropPattern = /(\w+)\?\s*:\s*([^;,\n}]+)(?=[;,\n}])/g
  const matches = [...content.matchAll(optionalPropPattern)]
  
  matches.forEach(match => {
    const [fullMatch, propName, propType] = match
    // Skip if already has undefined
    if (propType.includes('undefined')) return
    
    const newType = `${propName}?: ${propType.trim()} | undefined`
    content = content.replace(fullMatch, newType)
    modified = true
    console.log(`  ✓ Fixed optional property: ${propName}`)
  })

  // Pattern 2: Fix default values for optional props
  // Change "prop = undefined" to explicit undefined type
  const defaultUndefinedPattern = /(\w+)\s*=\s*undefined/g
  content = content.replace(defaultUndefinedPattern, (match, propName) => {
    modified = true
    console.log(`  ✓ Fixed default undefined: ${propName}`)
    return `${propName}: undefined`
  })

  // Pattern 3: Fix React component props with optional properties
  const componentPropsPattern = /interface\s+(\w+Props)\s*{([^}]+)}/g
  content = content.replace(componentPropsPattern, (match, propsName, propsBody) => {
    const fixedBody = propsBody.replace(
      /(\w+)\?\s*:\s*([^;,\n}]+)(?=[;,\n}])/g,
      (m, prop, type) => {
        if (!type.includes('undefined')) {
          console.log(`  ✓ Fixed prop in ${propsName}: ${prop}`)
          modified = true
          return `${prop}?: ${type.trim()} | undefined`
        }
        return m
      }
    )
    return `interface ${propsName} {${fixedBody}}`
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

// Find files with TS2375 errors
const filesWithOptionalErrors = Object.entries(report.files)
  .filter(([_, errors]) => errors.some(e => e.code === 'TS2375'))
  .map(([filePath]) => filePath)

console.log(`🔧 Fixing optional property issues in ${filesWithOptionalErrors.length} files...`)

// Fix each file
filesWithOptionalErrors.forEach(filePath => {
  console.log(`\n📝 Processing ${path.basename(filePath)}:`)
  fixOptionalProps(filePath)
})

console.log('\n✨ Done! Run TypeScript check again to verify fixes.')