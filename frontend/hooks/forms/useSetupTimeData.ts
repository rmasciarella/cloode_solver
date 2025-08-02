import { useState, useEffect, useCallback } from 'react'
import { optimizedTaskSetupTimeService, optimizedTaskService, machineService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'
import { performanceUtils } from '@/hooks/use-performance-monitor'

export type SetupTime = {
  setup_time_id: string
  from_optimized_task_id: string
  to_optimized_task_id: string
  machine_resource_id: string
  setup_time_minutes: number
  setup_type: string
  complexity_level: string
  requires_operator_skill: string | null
  requires_certification: boolean
  requires_supervisor_approval: boolean
  setup_cost: number
  efficiency_impact_percent: number
  created_at: string
  from_task?: { name: string }
  to_task?: { name: string }
  machine?: { name: string }
}

export type OptimizedTask = {
  optimized_task_id: string
  name: string
  pattern_id: string
  pattern_name: string
}

export type Machine = {
  machine_resource_id: string
  name: string
}

export function useSetupTimeData() {
  const [setupTimes, setSetupTimes] = useState<SetupTime[]>([])
  const [templateTasks, setTemplateTasks] = useState<OptimizedTask[]>([])
  const [machines, setMachines] = useState<Machine[]>([])
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const fetchSetupTimes = useCallback(async () => {
    setLoading(true)
    
    try {
      const { result } = await performanceUtils.measureAsync(
        async () => {
          const response = await optimizedTaskSetupTimeService.getAll()
          if (!response.success) {
            throw new Error(response.error || 'Failed to fetch setup times')
          }
          return response.data || []
        },
        'SetupTimeForm',
        'service_fetch_setup_times',
        { table: 'optimized_task_setup_times' }
      )
      
      setSetupTimes(result)
    } catch (error) {
      console.error('Error fetching setup times:', error)
      toast({
        title: "Error",
        description: "Failed to fetch setup times",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }, [toast])

  const fetchTemplateTasks = useCallback(async () => {
    try {
      const { result } = await performanceUtils.measureAsync(
        async () => {
          const response = await optimizedTaskService.getAllWithPatterns()
          if (!response.success) {
            throw new Error(response.error || 'Failed to fetch template tasks')
          }
          
          const formattedTasks = response.data?.map(task => ({
            optimized_task_id: task.optimized_task_id,
            name: task.name,
            pattern_id: task.pattern_id,
            pattern_name: (task.job_optimized_patterns as any)?.name || 'Unknown Pattern'
          })) || []
          
          return formattedTasks
        },
        'SetupTimeForm',
        'service_fetch_template_tasks',
        { table: 'optimized_tasks' }
      )
      
      setTemplateTasks(result)
    } catch (error) {
      console.error('Error fetching template tasks:', error)
    }
  }, [])

  const fetchMachines = useCallback(async () => {
    try {
      const { result } = await performanceUtils.measureAsync(
        async () => {
          const response = await machineService.getAll(true)
          if (!response.success) {
            throw new Error(response.error || 'Failed to fetch machines')
          }
          return response.data || []
        },
        'SetupTimeForm',
        'service_fetch_machines',
        { table: 'machines', filter: 'is_active=true' }
      )
      
      setMachines(result)
    } catch (error) {
      console.error('Error fetching machines:', error)
    }
  }, [])

  const deleteSetupTime = useCallback(async (id: string) => {
    try {
      const { duration: _duration } = await performanceUtils.measureAsync(
        async () => {
          const response = await optimizedTaskSetupTimeService.delete(id)
          if (!response.success) {
            throw new Error(response.error || 'Failed to delete setup time')
          }
        },
        'SetupTimeForm',
        'supabase_delete_setup_time',
        { setup_time_id: id }
      )

      toast({
        title: "Success",
        description: "Setup time deleted successfully"
      })
      
      await fetchSetupTimes()
    } catch (error) {
      console.error('Error deleting setup time:', error)
      toast({
        title: "Error",
        description: "Failed to delete setup time",
        variant: "destructive"
      })
      throw error
    }
  }, [toast, fetchSetupTimes])

  useEffect(() => {
    const loadData = async () => {
      await Promise.all([
        fetchSetupTimes(),
        fetchTemplateTasks(),
        fetchMachines()
      ])
    }
    
    loadData()
  }, [fetchSetupTimes, fetchTemplateTasks, fetchMachines])

  return {
    setupTimes,
    templateTasks,
    machines,
    loading,
    fetchSetupTimes,
    deleteSetupTime
  }
}