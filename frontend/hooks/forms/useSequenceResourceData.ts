"use client"

import { useState, useEffect, useCallback } from 'react'
import { sequenceResourceService, departmentService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'
import { Database } from '@/lib/database.types'

type SequenceResource = Database['public']['Tables']['sequence_resources']['Row']
type Department = Database['public']['Tables']['departments']['Row']

export function useSequenceResourceData() {
  const [sequenceResources, setSequenceResources] = useState<SequenceResource[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const fetchSequenceResources = useCallback(async () => {
    setLoading(true)
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
    } finally {
      setLoading(false)
    }
  }, [toast])

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
    fetchSequenceResources()
    fetchDepartments()
  }, [fetchSequenceResources, fetchDepartments])

  return {
    sequenceResources,
    departments,
    loading,
    fetchSequenceResources
  }
}
