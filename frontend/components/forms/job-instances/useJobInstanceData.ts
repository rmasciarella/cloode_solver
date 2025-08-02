"use client"

import { useState, useEffect, useCallback } from 'react'
import { jobInstanceService, departmentService, jobTemplateService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'

export function useJobInstanceData() {
  const [jobInstances, setJobInstances] = useState([])
  const [jobTemplates, setJobTemplates] = useState([])
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const fetchJobInstances = useCallback(async () => {
    setLoading(true)
    try {
      const response = await jobInstanceService.getAllWithPatterns()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch job instances')
      }
      setJobInstances(response.data || [])
    } catch (error) {
      console.error('Error fetching job instances:', error)
      toast({
        title: "Error",
        description: "Failed to fetch job instances",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }, [toast])

  const fetchJobTemplates = useCallback(async () => {
    try {
      const response = await jobTemplateService.getAll(true)  // Get only active templates
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch job templates')
      }
      // Map pattern_id to template_id for compatibility
      const mappedData = response.data?.map(item => ({
        template_id: item.pattern_id,
        name: item.name
      })) || []
      setJobTemplates(mappedData)
    } catch (error) {
      console.error('Error fetching job templates:', error)
    }
  }, [])

  const fetchDepartments = useCallback(async () => {
    try {
      const response = await departmentService.getAll(true)  // Get only active departments
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch departments')
      }
      setDepartments(response.data || [])
    } catch (error) {
      console.error('Error fetching departments:', error)
    }
  }, [])

  useEffect(() => {
    fetchJobInstances()
    fetchJobTemplates()
    fetchDepartments()
  }, [fetchJobInstances, fetchJobTemplates, fetchDepartments])

  return {
    jobInstances,
    jobTemplates,
    departments,
    loading,
    fetchJobInstances,
    fetchJobTemplates,
    fetchDepartments
  }
}
