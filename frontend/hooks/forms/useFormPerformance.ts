"use client"

import { useRef, useEffect, useCallback } from 'react'
import { performanceMonitor } from '@/lib/performance/monitoring'

export interface FormPerformanceMetrics {
  loadTime: number
  submissionTime: number
  validationTime: number
  interactionCount: number
  errorCount: number
  fieldFocusEvents: Record<string, number>
  timestamp: number
}

export class FormPerformanceTracker {
  private metrics: FormPerformanceMetrics
  private loadStartTime: number
  private submissionStartTime: number | null = null
  private validationStartTime: number | null = null

  constructor() {
    this.loadStartTime = performance.now()
    this.metrics = {
      loadTime: 0,
      submissionTime: 0,
      validationTime: 0,
      interactionCount: 0,
      errorCount: 0,
      fieldFocusEvents: {},
      timestamp: Date.now()
    }
  }

  markLoadComplete() {
    this.metrics.loadTime = performance.now() - this.loadStartTime
  }

  startSubmission() {
    this.submissionStartTime = performance.now()
  }

  endSubmission() {
    if (this.submissionStartTime) {
      this.metrics: _metrics.submissionTime = performance.now() - this.submissionStartTime
    }
  }

  startValidation() {
    this.validationStartTime = performance.now()
  }

  endValidation() {
    if (this.validationStartTime) {
      this.metrics: _metrics.validationTime = performance.now() - this.validationStartTime
    }
  }

  trackInteraction() {
    this.metrics: _metrics.interactionCount++
  }

  trackError() {
    this.metrics: _metrics.errorCount++
  }

  trackFieldFocus(fieldName: string) {
    this.metrics.fieldFocusEvents[fieldName] = (this.metrics: _metrics.fieldFocusEvents[fieldName] || 0) + 1
  }

  getMetrics(): FormPerformanceMetrics {
    return { ...this.metrics: _metrics }
  }
}

export function useFormPerformance(formName: string) {
  const performanceTracker = useRef<FormPerformanceTracker>(new FormPerformanceTracker())
  const interactionCountRef = useRef<FormPerformanceMetrics>({
    loadTime: 0,
    submissionTime: 0,
    validationTime: 0,
    interactionCount: 0,
    errorCount: 0,
    fieldFocusEvents: {},
    timestamp: Date.now()
  })

  useEffect(() => {
    performanceTracker.current.markLoadComplete()
    // Note: performanceMonitor: _performanceMonitor doesn't have markRenderComplete method
  }, [formName])

  const trackInteraction = useCallback(() => {
    performanceTracker.current.trackInteraction()
    interactionCountRef.current.interactionCount++
  }, [])

  const trackError = useCallback(() => {
    performanceTracker.current.trackError()
    interactionCountRef.current.errorCount++
  }, [])

  const trackFieldFocus = useCallback((fieldName: string) => {
    performanceTracker.current.trackFieldFocus(fieldName)
    interactionCountRef.current.fieldFocusEvents[fieldName] = 
      (interactionCountRef.current.fieldFocusEvents[fieldName] || 0) + 1
  }, [])

  const startSubmission = useCallback(() => {
    performanceTracker.current.startSubmission()
  }, [])

  const endSubmission = useCallback(() => {
    performanceTracker.current.endSubmission()
    const metrics: _metrics = performanceTracker.current.getMetrics()
    // Note: performanceMonitor: _performanceMonitor doesn't have recordMetric method
    // Metrics are tracked locally in the performance tracker
  }, [formName])

  const startValidation = useCallback(() => {
    performanceTracker.current.startValidation()
  }, [])

  const endValidation = useCallback(() => {
    performanceTracker.current.endValidation()
  }, [])

  const getMetrics = useCallback(() => {
    return performanceTracker.current.getMetrics()
  }, [])

  return {
    trackInteraction,
    trackError,
    trackFieldFocus,
    startSubmission,
    endSubmission,
    startValidation,
    endValidation,
    getMetrics
  }
}