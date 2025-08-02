"use client"

import { useCallback, useRef, useEffect } from 'react'

interface PerformanceConfig {
  trackFormSubmits?: boolean
  trackLoadTimes?: boolean
  trackErrors?: boolean
  sampleRate?: number // 0.1 = 10% sampling
  enableWebVitals?: boolean
}

interface PerformanceMetrics {
  formSubmitTime?: number
  loadTime?: number
  errorCount?: number
  interactionCount?: number
}

interface PerformanceTracker {
  startTiming: (operation: string) => () => void
  trackFormSubmit: (success: boolean, data: _data?: any) => void
  trackError: (error: Error, context?: string) => void
  trackInteraction: (type: string, details: _details?: any) => void
  getMetrics: () => PerformanceMetrics
}

const DEFAULT_CONFIG: PerformanceConfig = {
  trackFormSubmits: true,
  trackLoadTimes: true,
  trackErrors: true,
  sampleRate: 0.1, // 10% sampling
  enableWebVitals: true
}

export function useOptimizedPerformance(
  formName: string,
  config: PerformanceConfig = {}
): PerformanceTracker {
  const finalConfig = { ...DEFAULT_CONFIG, ...config }
  const metricsRef = useRef<PerformanceMetrics>({
    interactionCount: 0,
    errorCount: 0
  })
  const timingsRef = useRef<Map<string, number>>(new Map())

  // Check if this session should be sampled
  const shouldSample = useRef(Math.random() < finalConfig.sampleRate!)
  
  // Only track if sampling allows it
  if (!shouldSample.current) {
    return {
      startTiming: () => () => {},
      trackFormSubmit: () => {},
      trackError: () => {},
      trackInteraction: () => {},
      getMetrics: () => metricsRef.current
    }
  }

  const startTiming = useCallback((operation: string) => {
    if (!finalConfig.trackLoadTimes) return () => {}
    
    const startTime = performance.now()
    timingsRef.current.set(operation, startTime)
    
    return () => {
      const endTime = performance.now()
      const duration = endTime - startTime
      
      // Only log if operation took more than 100ms (significant enough)
      if (duration > 100) {
        console.debug(`[Performance] ${formName}: ${operation} took ${duration.toFixed(2)}ms`)
      }
      
      return duration
    }
  }, [formName, finalConfig.trackLoadTimes])

  const trackFormSubmit = useCallback((success: boolean, data?: any) => {
    if (!finalConfig.trackFormSubmits) return
    
    const startTime = timingsRef.current.get('form-submit')
    if (startTime) {
      const duration = performance.now() - startTime
      metricsRef.current.formSubmitTime = duration
      
      // Log significant submit times
      if (duration > 1000) {
        console.warn(`[Performance] ${formName}: Slow form submit (${duration.toFixed(2)}ms)`)
      }
    }
    
    // Track success/failure
    if (!success) {
      metricsRef.current.errorCount = (metricsRef.current.errorCount || 0) + 1
    }
  }, [formName, finalConfig.trackFormSubmits])

  const trackError = useCallback((error: Error, context?: string) => {
    if (!finalConfig.trackErrors) return
    
    metricsRef.current.errorCount = (metricsRef.current.errorCount || 0) + 1
    
    // Log error for debugging
    console.error(`[Performance] ${formName}: Error in ${context || 'unknown'}:`, error)
  }, [formName, finalConfig.trackErrors])

  const trackInteraction = useCallback((type: string, details?: any) => {
    // Very lightweight interaction tracking
    metricsRef.current.interactionCount = (metricsRef.current.interactionCount || 0) + 1
    
    // Only track if it's a significant interaction
    if (['form-submit', 'bulk-operation', 'data: _data-load'].includes(type)) {
      timingsRef.current.set(type, performance.now())
    }
  }, [])

  const getMetrics = useCallback(() => {
    return { ...metricsRef.current }
  }, [])

  // Track Core Web Vitals if enabled
  useEffect(() => {
    if (!finalConfig.enableWebVitals) return

    // Simple CLS tracking
    let cumulativeLayoutShift = 0
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) {
          cumulativeLayoutShift += (entry as any).value
        }
      }
    })

    try {
      observer.observe({ type: 'layout-shift', buffered: true })
    } catch (e) {
      // PerformanceObserver not supported
    }

    return () => {
      observer.disconnect()
      
      // Report significant CLS
      if (cumulativeLayoutShift > 0.1) {
        console.warn(`[Performance] ${formName}: High CLS detected (${cumulativeLayoutShift.toFixed(3)})`)
      }
    }
  }, [formName, finalConfig.enableWebVitals])

  // Track initial load time
  useEffect(() => {
    if (!finalConfig.trackLoadTimes) return
    
    const loadEndTime = performance.now()
    metricsRef.current.loadTime = loadEndTime
    
    // Report slow loads
    if (loadEndTime > 2000) {
      console.warn(`[Performance] ${formName}: Slow initial load (${loadEndTime.toFixed(2)}ms)`)
    }
  }, [formName, finalConfig.trackLoadTimes])

  return {
    startTiming,
    trackFormSubmit,
    trackError,
    trackInteraction,
    getMetrics
  }
}

// Helper hook for critical user journey tracking
export function useCriticalJourneyTracking(journeyName: string) {
  const tracker = useOptimizedPerformance(journeyName, {
    sampleRate: 1.0, // 100% sampling for critical journeys
    trackFormSubmits: true,
    trackErrors: true
  })

  const trackStep = useCallback((stepName: string) => {
    return tracker.startTiming(`journey-step-${stepName}`)
  }, [tracker])

  const trackJourneyComplete = useCallback((success: boolean, totalSteps: number) => {
    tracker.trackFormSubmit(success, { totalSteps })
  }, [tracker])

  return {
    trackStep,
    trackJourneyComplete,
    trackError: tracker.trackError
  }
}