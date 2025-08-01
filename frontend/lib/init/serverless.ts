/**
 * Serverless Environment Initialization
 * 
 * Ensures proper setup for Netlify Functions and other serverless environments.
 * This file should be imported at the top of any serverless function entry point.
 */

import { initializeErrorHandlers } from '@/lib/utils/error-handler'

let initialized = false

/**
 * Initialize serverless environment configurations
 */
export function initializeServerlessEnvironment() {
  // Prevent multiple initializations
  if (initialized || typeof window !== 'undefined') {
    return
  }
  
  initialized = true
  
  // Initialize global error handlers
  initializeErrorHandlers({
    logToConsole: true,
    captureStackTrace: process.env.NODE_ENV !== 'production',
    maxErrorsPerMinute: 100,
    shutdownOnCritical: false // Let Netlify handle restarts
  })
  
  // Set up any other serverless-specific configurations
  setupServerlessDefaults()
  
  console.log('[Serverless] Environment initialized successfully')
}

/**
 * Configure serverless-specific defaults
 */
function setupServerlessDefaults() {
  // Ensure timezone is consistent
  process.env.TZ = process.env.TZ || 'UTC'
  
  // Set default timeout warning
  const functionTimeout = parseInt(process.env.NETLIFY_FUNCTIONS_TIMEOUT || '10') * 1000
  if (functionTimeout > 0) {
    setTimeout(() => {
      console.warn(`[Serverless] Function approaching timeout (${functionTimeout}ms)`)
    }, functionTimeout - 1000)
  }
  
  // Ensure proper cleanup on function end
  process.on('beforeExit', () => {
    // Perform any cleanup tasks here
    console.log('[Serverless] Function execution completing')
  })
}

// Auto-initialize if this is a serverless environment
if (process.env.NETLIFY || process.env.AWS_LAMBDA_FUNCTION_NAME) {
  initializeServerlessEnvironment()
}