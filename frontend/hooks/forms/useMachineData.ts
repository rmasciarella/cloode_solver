"use client"

import { useState, useEffect, useCallback } from 'react'
import { machineService, departmentService, workCellService } from '@/lib/services'
import { Database } from '@/lib/database.types'
import { useOptimizedPerformance } from '@/hooks/useOptimizedPerformance'

type Machine = Database['public']['Tables']['machines']['Row']
type Department = Database['public']['Tables']['departments']['Row']
type WorkCell = Database['public']['Tables']['work_cells']['Row']

interface UseMachineDataReturn {
  machines: Machine[]
  departments: Department[]
  workCells: WorkCell[]
  filteredWorkCells: WorkCell[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  filterWorkCellsByDepartment: (departmentId: string | null) => void
}

export function useMachineData(): UseMachineDataReturn {
  const [machines, setMachines] = useState<Machine[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [workCells, setWorkCells] = useState<WorkCell[]>([])
  const [filteredWorkCells, setFilteredWorkCells] = useState<WorkCell[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const performanceTracker = useOptimizedPerformance('machine-data-hook')

  const fetchData = useCallback(async () => {
    const endTiming = performanceTracker.startTiming('data-fetch')
    
    try {
      setLoading(true)
      setError(null)

      const [machinesResponse, departmentsResponse, workCellsResponse] = await Promise.all([
        machineService.getAll(),
        departmentService.getAll(),
        workCellService.getAll()
      ])

      if (machinesResponse.error) {
        throw new Error(machinesResponse.error.message)
      }
      if (departmentsResponse.error) {
        throw new Error(departmentsResponse.error.message)
      }
      if (workCellsResponse.error) {
        throw new Error(workCellsResponse.error.message)
      }

      setMachines(machinesResponse.data || [])
      setDepartments(departmentsResponse.data || [])
      setWorkCells(workCellsResponse.data || [])
      setFilteredWorkCells(workCellsResponse.data || [])

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch data'
      setError(errorMessage)
      performanceTracker.trackError(err instanceof Error ? err : new Error(errorMessage), 'data-fetch')
    } finally {
      setLoading(false)
      endTiming()
    }
  }, [performanceTracker])

  const filterWorkCellsByDepartment = useCallback((departmentId: string | null) => {
    if (!departmentId) {
      setFilteredWorkCells(workCells)
    } else {
      const filtered = workCells.filter(wc => wc.department_id === departmentId)
      setFilteredWorkCells(filtered)
    }
  }, [workCells])

  const refetch = useCallback(async () => {
    await fetchData()
  }, [fetchData])

  // Initial data fetch
  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    machines,
    departments,
    workCells,
    filteredWorkCells,
    loading,
    error,
    refetch,
    filterWorkCellsByDepartment
  }
}