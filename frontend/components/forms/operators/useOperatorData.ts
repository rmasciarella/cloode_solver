"use client"

import { useState, useEffect } from 'react'
import { operatorService, departmentService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'

export function useOperatorData() {
  const [operators, setOperators] = useState([])
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const fetchOperators = async () => {
    setLoading(true)
    try {
      const response = await operatorService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch operators')
      }
      setOperators(response.data || [])
    } catch (error) {
      console.error('Error fetching operators:', error)
      toast({
        title: "Error",
        description: "Failed to fetch operators",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchDepartments = async () => {
    try {
      const response = await departmentService.getAll() // Get all departments, not just active
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch departments')
      }
      setDepartments(response.data || [])
    } catch (error) {
      console.error('Error fetching departments:', error)
    }
  }

  useEffect(() => {
    fetchOperators()
    fetchDepartments()
  }, [])

  return {
    operators,
    departments,
    loading,
    fetchOperators,
    fetchDepartments
  }
}
