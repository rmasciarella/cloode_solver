"use client"

import React from 'react'
import { Toaster } from '@/components/ui/toaster'
// Auth removed

interface AppProvidersProps {
  children: React.ReactNode
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <>
      {children}
      <Toaster />
    </>
  )
}