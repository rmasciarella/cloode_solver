/**
 * Next.js Instrumentation
 * 
 * This file is loaded once when the Next.js server starts.
 * Used to initialize serverless environment configurations.
 */

export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    // Initialize serverless environment for server-side code
    await import('./lib/init/serverless')
  }
}