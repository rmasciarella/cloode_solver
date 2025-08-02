"use client"

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouteBasedNavigation, shouldShowMigrationControls, logFeatureFlags } from '@/lib/config/features'
import HomeContent from './page-client'

export default function Home() {
  const [mounted, setMounted] = useState(false)
  const useNewNavigation = useRouteBasedNavigation()
  const showControls = shouldShowMigrationControls()

  useEffect(() => {
    setMounted(true)
    logFeatureFlags()
  }, [])

  // Show loading state during hydration
  if (!mounted) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Vulcan MES...</p>
        </div>
      </div>
    )
  }

  // Show migration controls in development
  if (showControls) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Migration Control Banner */}
        <div className="bg-blue-600 text-white p-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">Architecture Migration Controls</h2>
              <p className="text-blue-100 text-sm">
                Current Mode: {useNewNavigation ? 'Route-Based Navigation' : 'SPA Navigation'}
              </p>
            </div>
            <div className="flex gap-4">
              <Link
                href="/dashboard"
                className="bg-blue-700 hover:bg-blue-800 px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Dashboard (New)
              </Link>
              <Link
                href="/?spa=true"
                className="bg-blue-700 hover:bg-blue-800 px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                SPA Mode (Legacy)
              </Link>
            </div>
          </div>
        </div>

        {/* Content based on feature flag */}
        {useNewNavigation ? (
          <div className="py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
              <h1 className="text-4xl font-bold text-gray-900 mb-4">Welcome to Vulcan MES</h1>
              <p className="text-xl text-gray-600 mb-8">
                Manufacturing Execution System with Route-Based Architecture
              </p>
              <div className="space-y-4">
                <Link
                  href="/dashboard"
                  className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg text-lg font-medium transition-colors"
                >
                  Go to Dashboard
                </Link>
                <div className="text-sm text-gray-500">
                  Or navigate directly to any form using the sidebar
                </div>
              </div>
            </div>
          </div>
        ) : (
          <HomeContent />
        )}
      </div>
    )
  }

  // Production mode - use feature flag to determine navigation
  return useNewNavigation ? (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Welcome to Vulcan MES</h1>
        <p className="text-xl text-gray-600 mb-8">
          Manufacturing Execution System
        </p>
        <Link
          href="/dashboard"
          className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg text-lg font-medium transition-colors"
        >
          Go to Dashboard
        </Link>
      </div>
    </div>
  ) : (
    <HomeContent />
  )
}