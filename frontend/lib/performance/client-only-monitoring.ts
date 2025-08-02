/**
 * Client-only Performance Monitoring
 * This wrapper ensures performance monitoring only runs on the client
 * to prevent hydration mismatches
 */

class NoOpPerformanceMonitor {
  getMetrics() { return [] }
  getWebVitals() { return [] }
  getSlowQueries() { return [] }
  getAverageQueryTime() { return 0 }
  getPerformanceSummary() {
    return {
      totalQueries: 0,
      slowQueries: 0,
      averageQueryTime: 0,
      poorWebVitals: 0,
      lastUpdated: new Date().toISOString()
    }
  }
  clear() {}
}

// Export a no-op monitor for SSR, real monitor for client
let performanceMonitor: any;

if (typeof window === 'undefined') {
  // Server-side: use no-op implementation
  performanceMonitor = new NoOpPerformanceMonitor()
} else {
  // Client-side: use real implementation
  // Lazy load to ensure it's only loaded on client
  import('./monitoring').then((module) => {
    performanceMonitor = module.performanceMonitor
  })
  
  // Use no-op until real implementation loads
  performanceMonitor = new NoOpPerformanceMonitor()
}

export { performanceMonitor }