"use client"

import { useState, useEffect } from 'react'
import { workCellService, departmentService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'

export function useWorkCellData() {
  const [workCells, setWorkCells] = useState([])
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const fetchWorkCells = async () => {
    setLoading(true)
    
    try {
      const response = await workCellService.getAll()
      
      if (response.success && response.data) {
        setWorkCells(response.data)
      } else {
        const errorMsg = response.error || "Failed to fetch work cells"
        console.error('Error fetching work cells:', response.error)
        
        toast({
          title: "Error",
          description: errorMsg,
          variant: "destructive"
        })
      }
    } catch (error) {
      const errorMsg = String(error)
      
      toast({
        title: "Error",
        description: "Failed to fetch work cells",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchDepartments = async () => {
    try {
      const response = await departmentService.getAll(true) // activeOnly = true
      
      if (response.success && response.data) {
        setDepartments(response.data)
      } else {
        const errorMsg = response.error || "Failed to fetch departments"
        console.error('Error fetching departments:', response.error)
      }
    } catch (error) {
      const errorMsg = String(error)
      console.error('Error fetching departments:', errorMsg)
    }
  }

  useEffect(() => {
    const loadData = async () => {
      try {
        await Promise.all([
          fetchWorkCells(),
          fetchDepartments()
        ])
      } catch (error) {
        console.error('Error loading form data:', error)
      }
    }
    
    loadData()
  }, [])

  return {
    workCells,
    departments,
    loading,
    fetchWorkCells,
    fetchDepartments
  }
}
