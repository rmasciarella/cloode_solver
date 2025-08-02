"use client"

import { useState, useEffect, useCallback } from 'react'
import { optimizedTaskService, jobTemplateService, departmentService, sequenceResourceService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'

type OptimizedTask = {
  optimized_task_id: string
  pattern_id: string
  name: string
  position: number
  department_id: string | null
  is_unattended: boolean
  is_setup: boolean
  sequence_id: string | null
  min_operators: number
  max_operators: number
  operator_efficiency_curve: string | null
  created_at: string
}

type JobOptimizedPattern = {
  pattern_id: string
  name: string
}

type Department = {
  department_id: string
  name: string
  code: string
}

type SequenceResource = {
  sequence_id: string
  name: string
}

export function useTemplateTaskData() {
  const [optimizedTasks, setOptimizedTasks] = useState<OptimizedTask[]>([])
  const [jobOptimizedPatterns, setJobOptimizedPatterns] = useState<JobOptimizedPattern[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [sequenceResources, setSequenceResources] = useState<SequenceResource[]>([])
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const fetchOptimizedTasks = useCallback(async () => {
    setLoading(true)
    try {
      const response = await optimizedTaskService.getAllWithPatterns()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch optimized tasks')
      }
      setOptimizedTasks(response.data || [])
    } catch (error) {
      console.error('Error fetching optimized tasks:', error)
      toast({
        title: "Error",
        description: "Failed to fetch optimized tasks",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }, [toast])

  const fetchJobOptimizedPatterns = useCallback(async () => {
    try {
      const response = await jobTemplateService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch job optimized patterns')
      }
      setJobOptimizedPatterns(response.data || [])
    } catch (error) {
      console.error('Error fetching job optimized patterns:', error)
      toast({
        title: "Error",
        description: "Failed to fetch job optimized patterns",
        variant: "destructive"
      })
    }
  }, [toast])

  const fetchDepartments = useCallback(async () => {
    try {
      const response = await departmentService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch departments')
      }
      setDepartments(response.data || [])
    } catch (error) {
      console.error('Error fetching departments:', error)
      toast({
        title: "Error",
        description: "Failed to fetch departments",
        variant: "destructive"
      })
    }
  }, [toast])

  const fetchSequenceResources = useCallback(async () => {
    try {
      const response = await sequenceResourceService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch sequence resources')
      }
      setSequenceResources(response.data || [])
    } catch (error) {
      console.error('Error fetching sequence resources:', error)
      toast({
        title: "Error",
        description: "Failed to fetch sequence resources",
        variant: "destructive"
      })
    }
  }, [toast])

  const fetchAllData = useCallback(async () => {
    await Promise.all([
      fetchOptimizedTasks(),
      fetchJobOptimizedPatterns(),
      fetchDepartments(),
      fetchSequenceResources()
    ])
  }, [fetchOptimizedTasks, fetchJobOptimizedPatterns, fetchDepartments, fetchSequenceResources])

  useEffect(() => {
    fetchAllData()
  }, [fetchAllData])

  return {
    optimizedTasks,
    jobOptimizedPatterns,
    departments,
    sequenceResources,
    loading,
    fetchOptimizedTasks,
    fetchAllData
  }
}
