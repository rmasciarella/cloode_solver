/**
 * Feature Flag Configuration
 * 
 * Controls which features and architectural approaches are enabled.
 * Used for gradual migration and A/B testing.
 */

export interface FeatureFlags {
  // Architecture Migration Flags
  useRouteBasedNavigation: boolean
  enableCodeSplitting: boolean
  enableSSROptimization: boolean
  
  // Performance Monitoring Flags  
  enablePerformanceMonitoring: boolean
  enableBundleAnalysis: boolean
  
  // Development Flags
  showMigrationControls: boolean
  enableDebugMode: boolean
}

// Default feature flag values
const _defaultFlags: FeatureFlags = {
  useRouteBasedNavigation: false, // Start with SPA, gradually migrate
  enableCodeSplitting: false,
  enableSSROptimization: false,
  enablePerformanceMonitoring: true,
  enableBundleAnalysis: false,
  showMigrationControls: true, // Show controls in development
  enableDebugMode: false,
}

// Environment-based overrides
const getFeatureFlags = (): FeatureFlags => {
  const isDevelopment = process.env.NODE_ENV === 'development'
  const isProduction: _isProduction = process.env.NODE_ENV === 'production'
  
  return {
    useRouteBasedNavigation: process.env.NEXT_PUBLIC_USE_ROUTE_NAVIGATION === 'true' || false,
    enableCodeSplitting: process.env.NEXT_PUBLIC_ENABLE_CODE_SPLITTING === 'true' || false,
    enableSSROptimization: process.env.NEXT_PUBLIC_ENABLE_SSR_OPTIMIZATION === 'true' || false,
    enablePerformanceMonitoring: isDevelopment || process.env.NEXT_PUBLIC_ENABLE_PERFORMANCE_MONITORING === 'true',
    enableBundleAnalysis: process.env.NEXT_PUBLIC_ENABLE_BUNDLE_ANALYSIS === 'true' || false,
    showMigrationControls: isDevelopment || process.env.NEXT_PUBLIC_SHOW_MIGRATION_CONTROLS === 'true',
    enableDebugMode: isDevelopment || process.env.NEXT_PUBLIC_ENABLE_DEBUG_MODE === 'true',
  }
}

export const featureFlags = getFeatureFlags()

// Utility functions for feature checking
export const useRouteBasedNavigation = () => featureFlags.useRouteBasedNavigation
export const isCodeSplittingEnabled = () => featureFlags.enableCodeSplitting
export const isSSROptimizationEnabled = () => featureFlags.enableSSROptimization
export const isPerformanceMonitoringEnabled = () => featureFlags.enablePerformanceMonitoring
export const shouldShowMigrationControls = () => featureFlags.showMigrationControls

// Migration helper to check if we should use new architecture
export const shouldUseNewArchitecture = () => {
  return featureFlags.useRouteBasedNavigation && featureFlags.enableCodeSplitting
}

// Development utilities
export const logFeatureFlags = () => {
  if (featureFlags.enableDebugMode) {
    console.group('🚀 Feature Flags Configuration')
    console.table(featureFlags)
    console.groupEnd()
  }
}