#!/usr/bin/env node

/**
 * TypeScript Error Fixing Script for Phase 3 Refactor
 * 
 * This script helps identify and fix common TypeScript strict mode errors:
 * - Unused imports
 * - Unused variables  
 * - Missing return types
 * - Implicit any types
 * - Optional property type issues
 */

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

const FRONTEND_DIR = process.cwd()
const COMPONENTS_DIR = path.join(FRONTEND_DIR, 'components')

// Common patterns for fixing TypeScript errors
const ERROR_PATTERNS = {
  // Unused imports: import { A, B } from 'module' where A is unused
  UNUSED_IMPORT: /error TS6133: '(\w+)' is declared but its value is never read\./,
  
  // Missing return type
  MISSING_RETURN: /error TS7030: Not all code paths return a value\./,
  
  // Implicit any
  IMPLICIT_ANY: /error TS7053: Element implicitly has an 'any' type/,
  
  // Unused parameters
  UNUSED_PARAM: /error TS6133: '(\w+)' is declared but its value is never read\./,
  
  // Optional property issues
  OPTIONAL_PROPERTY: /error TS2375: Type .+ is not assignable to type .+ with 'exactOptionalPropertyTypes: true'/
}

function runTypeScriptCheck() {
  try {
    const result = execSync('npx tsc --noEmit --maxNodeModuleJsDepth 0', { 
      encoding: 'utf8',
      cwd: FRONTEND_DIR 
    })
    return { success: true, output: result }
  } catch (error) {
    return { success: false, output: error.stdout || error.message }
  }
}

function analyzeErrors(output) {
  const lines = output.split('\n').filter(line => line.includes('error TS'))
  
  const errorsByFile = {}
  lines.forEach(line => {
    const match = line.match(/^(.+?)\(\d+,\d+\): error (TS\d+): (.+)$/)
    if (match) {
      const [, filePath, errorCode, message] = match
      if (!errorsByFile[filePath]) {
        errorsByFile[filePath] = []
      }
      errorsByFile[filePath].push({ code: errorCode, message, line })
    }
  })
  
  return errorsByFile
}

function generateFixSuggestions(errorsByFile) {
  const suggestions = []
  
  Object.entries(errorsByFile).forEach(([filePath, errors]) => {
    const fileContent = fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8') : ''
    
    errors.forEach(error => {
      switch (error.code) {
        case 'TS6133':
          if (error.message.includes('is declared but its value is never read')) {
            const variable = error.message.match(/'(\w+)'/)?.[1]
            if (variable) {
              suggestions.push({
                file: filePath,
                type: 'unused-variable',
                variable,
                suggestion: `Remove unused variable '${variable}' or prefix with underscore: '_${variable}'`
              })
            }
          }
          break
          
        case 'TS7030':
          suggestions.push({
            file: filePath,
            type: 'missing-return',
            suggestion: 'Add explicit return statement or return type annotation'
          })
          break
          
        case 'TS7053':
          suggestions.push({
            file: filePath,
            type: 'implicit-any',
            suggestion: 'Add explicit type annotations to avoid implicit any'
          })
          break
          
        case 'TS2375':
          suggestions.push({
            file: filePath,
            type: 'optional-property',
            suggestion: 'Fix optional property types for exactOptionalPropertyTypes compliance'
          })
          break
      }
    })
  })
  
  return suggestions
}

function createFixReport(errorsByFile, suggestions) {
  const report = {
    summary: {
      totalFiles: Object.keys(errorsByFile).length,
      totalErrors: Object.values(errorsByFile).reduce((sum, errors) => sum + errors.length, 0),
      errorsByType: {}
    },
    files: errorsByFile,
    suggestions,
    priority: {
      high: suggestions.filter(s => ['implicit-any', 'optional-property'].includes(s.type)),
      medium: suggestions.filter(s => ['missing-return'].includes(s.type)),
      low: suggestions.filter(s => ['unused-variable'].includes(s.type))
    }
  }
  
  // Count errors by type
  Object.values(errorsByFile).flat().forEach(error => {
    const type = error.code
    report.summary.errorsByType[type] = (report.summary.errorsByType[type] || 0) + 1
  })
  
  return report
}

function main() {
  console.log('🔍 Running TypeScript strict mode check...')
  
  const { success, output } = runTypeScriptCheck()
  
  if (success) {
    console.log('✅ No TypeScript errors found!')
    return
  }
  
  console.log('📝 Analyzing TypeScript errors...')
  const errorsByFile = analyzeErrors(output)
  const suggestions = generateFixSuggestions(errorsByFile)
  const report = createFixReport(errorsByFile, suggestions)
  
  // Write detailed report
  const reportPath = path.join(FRONTEND_DIR, 'typescript-error-report.json')
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2))
  
  // Display summary
  console.log('\n📊 TypeScript Error Summary:')
  console.log(`   Total files with errors: ${report.summary.totalFiles}`)
  console.log(`   Total errors: ${report.summary.totalErrors}`)
  console.log('\n   Errors by type:')
  Object.entries(report.summary.errorsByType).forEach(([type, count]) => {
    console.log(`     ${type}: ${count}`)
  })
  
  console.log('\n🚨 Priority Fixes:')
  console.log(`   High priority: ${report.priority.high.length} errors`)
  console.log(`   Medium priority: ${report.priority.medium.length} errors`)
  console.log(`   Low priority: ${report.priority.low.length} errors`)
  
  // Show top priority fixes
  console.log('\n🔧 Top Priority Fixes:')
  report.priority.high.slice(0, 5).forEach((suggestion, i) => {
    console.log(`   ${i + 1}. ${path.basename(suggestion.file)}: ${suggestion.suggestion}`)
  })
  
  console.log(`\n📄 Full report saved to: ${reportPath}`)
  console.log('\n💡 To fix specific files, run:')
  console.log('   npx tsc --noEmit [file-path]')
  
  process.exit(1)
}

if (require.main === module) {
  main()
}