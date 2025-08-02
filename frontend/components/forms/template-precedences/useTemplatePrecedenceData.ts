"use client"

import { useState, useEffect, useCallback } from 'react'
import { optimizedPrecedenceService, optimizedTaskService, jobTemplateService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'

type TemplatePrecedence = {
  precedence_id: string
  pattern_id: string
  predecessor_task_id: string
  successor_task_id: string
  created_at: string
  // These fields may not exist in the database yet
  min_delay_minutes?: number
  max_delay_minutes?: number | null
  requires_department_transfer?: boolean
  transfer_time_minutes?: number
}

type OptimizedTask = {
  optimized_task_id: string
  name: string
  pattern_id: string
  pattern_name: string
}

type JobOptimizedPattern = {
  pattern_id: string
  name: string
}

export function useTemplatePrecedenceData() {
  const [templatePrecedences, setTemplatePrecedences] = useState<TemplatePrecedence[]>([])
  const [optimizedTasks, setOptimizedTasks] = useState<OptimizedTask[]>([])
  const [patterns, setPatterns] = useState<JobOptimizedPattern[]>([])
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const fetchTemplatePrecedences = useCallback(async () => {
    setLoading(true)
    try {
      const response = await optimizedPrecedenceService.getAll()
      if (!response.success) {
        // If table doesn't exist, just set empty data instead of throwing error
        if (response.error?.includes('42703') || response.error?.includes('42P01')) {
          console.warn('optimized_precedences table does not exist yet:', response.error)
          setTemplatePrecedences([])
          return
        }
        throw new Error(response.error || 'Failed to fetch template precedences')
      }
      setTemplatePrecedences(response.data || [])
    } catch (error: any) {
      console.error('Error fetching template precedences:', error)
      console.error('Error details:', {
        message: error?.message,
        details: error?.details,
        hint: error?.hint,
        code: error?.code
      })
      toast({
        title: "Warning",
        description: "Template precedences table not available yet",
        variant: "default"
      })
      setTemplatePrecedences([])
    } finally {
      setLoading(false)
    }
  }, [toast])

  const fetchOptimizedTasks = useCallback(async () => {
    try {
      const response = await optimizedTaskService.getAllWithPatterns()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch optimized tasks')
      }
      
      const formattedTasks = response.data?.map(task => ({
        optimized_task_id: task.optimized_task_id,
        name: task.name,
        pattern_id: task.pattern_id,
        pattern_name: (task.job_optimized_patterns as any)?.name || 'Unknown Pattern'
      })) || []
      
      setOptimizedTasks(formattedTasks)
    } catch (error) {
      console.error('Error fetching optimized tasks:', error)
      toast({
        title: "Error",
        description: "Failed to fetch optimized tasks",
        variant: "destructive"
      })
    }
  }, [toast])

  const fetchPatterns = useCallback(async () => {
    try {
      const response = await jobTemplateService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch patterns')
      }
      setPatterns(response.data || [])
    } catch (error) {
      console.error('Error fetching patterns:', error)
      toast({
        title: "Error",
        description: "Failed to fetch patterns",
        variant: "destructive"
      })
    }
  }, [toast])

  const fetchAllData = useCallback(async () => {
    await Promise.all([
      fetchTemplatePrecedences(),
      fetchOptimizedTasks(),
      fetchPatterns()
    ])
  }, [fetchTemplatePrecedences, fetchOptimizedTasks, fetchPatterns])

  useEffect(() => {
    fetchAllData()
  }, [fetchAllData])

  return {
    templatePrecedences,
    optimizedTasks,
    patterns,
    loading,
    fetchTemplatePrecedences,
    fetchAllData
  }
}
