/**
 * Global Error Handler for Serverless Environment
 * 
 * Prevents function crashes from unhandled errors and provides
 * centralized error logging and recovery mechanisms.
 */

// Error reporting configuration
interface ErrorConfig {
  logToConsole: boolean
  captureStackTrace: boolean
  maxErrorsPerMinute: number
  shutdownOnCritical: boolean
}

const defaultConfig: ErrorConfig = {
  logToConsole: true,
  captureStackTrace: true,
  maxErrorsPerMinute: 100,
  shutdownOnCritical: false
}

// Track error rates to prevent log flooding
const errorCounts = new Map<string, number>()
let errorResetInterval: NodeJS.Timeout | null = null

/**
 * Initialize global error handlers for serverless environment
 */
export function initializeErrorHandlers(config: Partial<ErrorConfig> = {}) {
  const finalConfig = { ...defaultConfig, ...config }
  
  // Only initialize in server-side environment
  if (typeof window !== 'undefined') {
    return
  }

  // Handle uncaught exceptions
  process.on('uncaughtException', (error: Error) => {
    handleError('uncaughtException', error, finalConfig)
  })

  // Handle unhandled promise rejections
  process.on('unhandledRejection', (reason: any, _promise: Promise<any>) => {
    const error = reason instanceof Error ? reason : new Error(String(reason))
    handleError('unhandledRejection', error, finalConfig)
  })

  // Reset error counts every minute
  if (!errorResetInterval) {
    errorResetInterval = setInterval(() => {
      errorCounts.clear()
    }, 60000)
  }

  // Cleanup on process exit
  process.on('exit', () => {
    if (errorResetInterval) {
      clearInterval(errorResetInterval)
      errorResetInterval = null
    }
  })
}

/**
 * Central error handling logic
 */
function handleError(type: string, error: Error, config: ErrorConfig) {
  const errorKey = `${type}:${error.message}`
  const currentCount = errorCounts.get(errorKey) || 0
  
  // Check rate limiting
  if (currentCount >= config.maxErrorsPerMinute) {
    return // Suppress error to prevent log flooding
  }
  
  errorCounts.set(errorKey, currentCount + 1)
  
  // Format error for logging
  const errorInfo = {
    type,
    message: error.message,
    stack: config.captureStackTrace ? error.stack : undefined,
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV,
    function: process.env.NETLIFY_FUNCTION_NAME || 'unknown'
  }
  
  // Log to console if enabled
  if (config.logToConsole) {
    console.error(`[GLOBAL ERROR HANDLER] ${type}:`, errorInfo)
  }
  
  // In production, you might want to send to an error tracking service
  if (process.env.NODE_ENV === 'production') {
    // Example: sendToSentry(errorInfo)
    // Example: sendToDatadog(errorInfo)
  }
  
  // Critical errors might warrant function shutdown
  if (config.shutdownOnCritical && isCriticalError(error)) {
    console.error('[CRITICAL ERROR] Shutting down function gracefully')
    process.exit(1)
  }
}

/**
 * Determine if an error is critical enough to warrant shutdown
 */
function isCriticalError(error: Error): boolean {
  const criticalPatterns = [
    /out of memory/i,
    /maximum call stack/i,
    /ENOSPC/i, // No space left on device
    /EMFILE/i, // Too many open files
  ]
  
  return criticalPatterns.some(pattern => pattern.test(error.message))
}

/**
 * Wrap an async function with error handling
 */
export function withErrorHandling<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  context?: string
): T {
  return (async (...args: Parameters<T>) => {
    try {
      return await fn(...args)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      console.error(`[ERROR in ${context || fn.name}]:`, errorMessage)
      throw error // Re-throw to maintain error propagation
    }
  }) as T
}

/**
 * Create a safe wrapper for serverless handlers
 */
export function createSafeHandler<T extends (...args: any[]) => Promise<any>>(
  handler: T
): T {
  return withErrorHandling(handler, 'ServerlessHandler')
}