"use client"

import { useState, useEffect, useCallback } from 'react'
import { businessCalendarService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'

export function useBusinessCalendarData() {
  const [businessCalendars, setBusinessCalendars] = useState([])
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const fetchBusinessCalendars = useCallback(async () => {
    const fetchStart = Date.now()
    setLoading(true)
    
    try {
      const response = await businessCalendarService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch business calendars')
      }
      setBusinessCalendars(response.data || [])
      
      // Track data fetch performance
      const fetchDuration = Date.now() - fetchStart
      if (process.env.NODE_ENV === 'development') {
        console.log(`[FORM-PERF] BusinessCalendarForm.fetchData: ${fetchDuration}ms`)
      }
    } catch (error) {
      console.error('Error fetching business calendars:', error)
      toast({
        title: "Error",
        description: "Failed to fetch business calendars",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    fetchBusinessCalendars()
  }, [fetchBusinessCalendars])

  return {
    businessCalendars,
    loading,
    fetchBusinessCalendars
  }
}
