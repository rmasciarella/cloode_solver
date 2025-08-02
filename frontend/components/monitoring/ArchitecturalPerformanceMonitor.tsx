"use client"

import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import { isPerformanceMonitoringEnabled, useRouteBasedNavigation } from '@/lib/config/features'

interface PerformanceMetrics {
  navigationMode: 'SPA' | 'Route-Based'
  routeLoadTime: number
  bundleSize: number
  timeToInteractive: number
  firstContentfulPaint: number
  cumulativeLayoutShift: number
  memoryUsage: number
  timestamp: number
}

interface PerformanceMonitorProps {
  routeName?: string
  formComponent?: string
}

export function ArchitecturalPerformanceMonitor({ 
  routeName: _routeName, 
  formComponent 
}: PerformanceMonitorProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null)
  const [isVisible, setIsVisible] = useState(false)
  const pathname = usePathname()
  const useRoutes = useRouteBasedNavigation()
  const monitoringEnabled = isPerformanceMonitoringEnabled()

  useEffect(() => {
    if (!monitoringEnabled) return

    const startTime = performance.now()
    
    // Measure route load performance
    const measurePerformance = () => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      const paintEntries = performance.getEntriesByType('paint')
      const fcp = paintEntries.find(entry => entry.name === 'first-contentful-paint')
      
      // Estimate bundle size (simplified)
      const bundleSize = performance.getEntriesByType('resource')
        .filter(entry => entry.name.includes('.js') || entry.name.includes('.css'))
        .reduce((total, entry) => total + (entry.transferSize || 0), 0)

      // Memory usage (if available)
      const memoryUsage = (performance as any).memory?.usedJSHeapSize || 0

      const newMetrics: PerformanceMetrics = {
        navigationMode: useRoutes ? 'Route-Based' : 'SPA',
        routeLoadTime: performance.now() - startTime,
        bundleSize: bundleSize,
        timeToInteractive: navigation?.loadEventEnd - navigation?.loadEventStart || 0,
        firstContentfulPaint: fcp?.startTime || 0,
        cumulativeLayoutShift: 0, // Would need CLS observer
        memoryUsage: memoryUsage,
        timestamp: Date.now(),
      }

      setMetrics(newMetrics)
      
      // Log metrics for analysis
      console.group(`🚀 Architecture Performance - ${newMetrics.navigationMode}`)
      console.table(newMetrics)
      console.groupEnd()

      // Store metrics for comparison
      storeMetrics(newMetrics)
    }

    // Measure after component is mounted and interactive
    const timer = setTimeout(measurePerformance, 100)
    
    return () => clearTimeout(timer)
  }, [pathname, useRoutes, monitoringEnabled])

  const storeMetrics = (metrics: PerformanceMetrics) => {
    try {
      const existingMetrics = JSON.parse(localStorage.getItem('vulcan-perf-metrics') || '[]')
      const updatedMetrics = [...existingMetrics, metrics].slice(-50) // Keep last 50 measurements
      localStorage.setItem('vulcan-perf-metrics', JSON.stringify(updatedMetrics))
    } catch (error) {
      console.warn('Failed to store performance metrics:', error)
    }
  }

  const exportMetrics = () => {
    try {
      const allMetrics = JSON.parse(localStorage.getItem('vulcan-perf-metrics') || '[]')
      const blob = new Blob([JSON.stringify(allMetrics, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `vulcan-performance-metrics-${Date.now()}.json`
      link.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export metrics:', error)
    }
  }

  const clearMetrics = () => {
    localStorage.removeItem('vulcan-perf-metrics')
    setMetrics(null)
  }

  if (!monitoringEnabled || !metrics) return null

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Toggle Button */}
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-full shadow-lg transition-colors mb-2"
        title="Performance Monitor"
      >
        📊
      </button>

      {/* Performance Panel */}
      {isVisible && (
        <div className="bg-white border border-gray-300 rounded-lg shadow-xl p-4 w-80 max-h-96 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">Performance Monitor</h3>
            <button
              onClick={() => setIsVisible(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Mode:</span>
              <span className={`font-medium ${
                metrics.navigationMode === 'Route-Based' ? 'text-green-600' : 'text-blue-600'
              }`}>
                {metrics.navigationMode}
              </span>
            </div>

            <div className="flex justify-between">
              <span className="text-gray-600">Route Load:</span>
              <span className="font-mono">{metrics.routeLoadTime.toFixed(2)}ms</span>
            </div>

            <div className="flex justify-between">
              <span className="text-gray-600">Bundle Size:</span>
              <span className="font-mono">{(metrics.bundleSize / 1024).toFixed(1)}KB</span>
            </div>

            <div className="flex justify-between">
              <span className="text-gray-600">Time to Interactive:</span>
              <span className="font-mono">{metrics.timeToInteractive.toFixed(2)}ms</span>
            </div>

            <div className="flex justify-between">
              <span className="text-gray-600">First Contentful Paint:</span>
              <span className="font-mono">{metrics.firstContentfulPaint.toFixed(2)}ms</span>
            </div>

            {metrics.memoryUsage > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-600">Memory Usage:</span>
                <span className="font-mono">{(metrics.memoryUsage / 1024 / 1024).toFixed(1)}MB</span>
              </div>
            )}

            <div className="pt-3 border-t border-gray-200 space-y-2">
              <button
                onClick={exportMetrics}
                className="w-full bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs transition-colors"
              >
                Export Metrics
              </button>
              <button
                onClick={clearMetrics}
                className="w-full bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs transition-colors"
              >
                Clear Data
              </button>
            </div>

            <div className="text-xs text-gray-500 pt-2 border-t border-gray-200">
              Route: {pathname}
              {formComponent && <><br />Form: {formComponent}</>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}