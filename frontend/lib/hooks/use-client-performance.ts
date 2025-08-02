/**
 * Client-only performance monitoring wrapper
 * Provides a safe wrapper around performance monitoring that only runs on the client
 */

import { useFormPerformanceMonitoring as useFormPerformanceMonitoringImpl } from './form-performance.hooks'

// No-op implementation for server-side rendering
const noOpTracker = {
  loadTime: null,
  firstInteraction: null,
  submissionTime: null,
  validationTime: null,
  errorCount: 0,
  interactionCount: 0,
  fieldFocusCount: {},
  validationErrorCount: {},
  trackInteraction: () => {},
  trackValidation: () => {},
  startValidation: () => {},
  endValidation: () => {},
  trackSubmissionStart: () => {},
  trackSubmissionEnd: () => {},
  finalizeMetrics: () => {},
  startSubmission: () => {},
  recordValidationComplete: () => {},
  recordInteraction: () => {},
  reportMetric: () => {},
  getFormSummary: () => null,
  isSlowLoading: false,
  isSlowSubmission: false,
  hasHighErrorRate: false
}

export function useClientFormPerformanceMonitoring(formName: string) {
  if (typeof window === 'undefined') {
    // Return no-op implementation for SSR
    return noOpTracker
  }
  
  // Use the real implementation on client
  return useFormPerformanceMonitoringImpl(formName)
}