import { createBrowserClient } from '@supabase/ssr'
import { Database, OptimizedTaskMode, MachineTaskMode } from '../database.types'

const supabase = createBrowserClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export class TaskModeService {
  
  /**
   * Get all machine modes available for a specific task
   */
  async getTaskModes(taskId: string): Promise<MachineTaskMode[]> {
    const { data, error } = await supabase
      .from('optimized_task_modes')
      .select(`
        *,
        machines!inner (
          id,
          name,
          status,
          capacity_hours,
          cost_per_hour,
          work_cells!inner (
            id,
            name,
            active
          )
        )
      `)
      .eq('optimized_task_id', taskId)
      .eq('machines.status', 'active')
      .eq('machines.work_cells.active', true)
      .order('preferred', { ascending: false })
      .order('cost_per_hour', { ascending: true })

    if (error) {
      throw new Error(`Failed to get task modes: ${error.message}`)
    }

    return (data || []).map(mode => ({
      machine_id: mode.machine_id,
      machine_name: mode.machines.name,
      processing_time: mode.processing_time,
      setup_time: mode.setup_time,
      cost_per_hour: mode.cost_per_hour,
      energy_consumption: mode.energy_consumption,
      preferred: mode.preferred,
      available: mode.machines.status === 'active'
    }))
  }

  /**
   * Create a new task mode (machine assignment option)
   */
  async createTaskMode(taskMode: {
    optimized_task_id: string
    machine_id: string
    processing_time: number
    setup_time: number
    cost_per_hour: number
    energy_consumption?: number
    preferred?: boolean
  }): Promise<OptimizedTaskMode> {
    const { data, error } = await supabase
      .from('optimized_task_modes')
      .insert({
        optimized_task_id: taskMode.optimized_task_id,
        machine_id: taskMode.machine_id,
        processing_time: taskMode.processing_time,
        setup_time: taskMode.setup_time,
        cost_per_hour: taskMode.cost_per_hour,
        energy_consumption: taskMode.energy_consumption || null,
        preferred: taskMode.preferred || false
      })
      .select()
      .single()

    if (error) {
      throw new Error(`Failed to create task mode: ${error.message}`)
    }

    return data
  }

  /**
   * Update a task mode
   */
  async updateTaskMode(
    modeId: string, 
    updates: Partial<Pick<OptimizedTaskMode, 'processing_time' | 'setup_time' | 'cost_per_hour' | 'energy_consumption' | 'preferred'>>
  ): Promise<OptimizedTaskMode> {
    const { data, error } = await supabase
      .from('optimized_task_modes')
      .update(updates)
      .eq('id', modeId)
      .select()
      .single()

    if (error) {
      throw new Error(`Failed to update task mode: ${error.message}`)
    }

    return data
  }

  /**
   * Delete a task mode
   */
  async deleteTaskMode(modeId: string): Promise<void> {
    const { error } = await supabase
      .from('optimized_task_modes')
      .delete()
      .eq('id', modeId)

    if (error) {
      throw new Error(`Failed to delete task mode: ${error.message}`)
    }
  }

  /**
   * Get all task modes for a pattern (bulk operation)
   */
  async getPatternTaskModes(patternId: string): Promise<Map<string, MachineTaskMode[]>> {
    const { data, error } = await supabase
      .from('optimized_task_modes')
      .select(`
        *,
        optimized_tasks!inner (
          id,
          name,
          pattern_id
        ),
        machines!inner (
          id,
          name,
          status,
          capacity_hours,
          cost_per_hour,
          work_cells!inner (
            id,
            name,
            active
          )
        )
      `)
      .eq('optimized_tasks.pattern_id', patternId)
      .eq('machines.status', 'active')
      .eq('machines.work_cells.active', true)
      .order('optimized_task_id')
      .order('preferred', { ascending: false })
      .order('cost_per_hour', { ascending: true })

    if (error) {
      throw new Error(`Failed to get pattern task modes: ${error.message}`)
    }

    // Group by task ID
    const taskModeMap = new Map<string, MachineTaskMode[]>()
    
    for (const mode of data || []) {
      const taskId = mode.optimized_task_id
      
      if (!taskModeMap.has(taskId)) {
        taskModeMap.set(taskId, [])
      }
      
      taskModeMap.get(taskId)!.push({
        machine_id: mode.machine_id,
        machine_name: mode.machines.name,
        processing_time: mode.processing_time,
        setup_time: mode.setup_time,
        cost_per_hour: mode.cost_per_hour,
        energy_consumption: mode.energy_consumption,
        preferred: mode.preferred,
        available: mode.machines.status === 'active'
      })
    }

    return taskModeMap
  }

  /**
   * Bulk create task modes for a pattern
   */
  async createPatternTaskModes(taskModes: Array<{
    optimized_task_id: string
    machine_id: string
    processing_time: number
    setup_time: number
    cost_per_hour: number
    energy_consumption?: number
    preferred?: boolean
  }>): Promise<OptimizedTaskMode[]> {
    
    const { data, error } = await supabase
      .from('optimized_task_modes')
      .insert(taskModes.map(mode => ({
        optimized_task_id: mode.optimized_task_id,
        machine_id: mode.machine_id,
        processing_time: mode.processing_time,
        setup_time: mode.setup_time,
        cost_per_hour: mode.cost_per_hour,
        energy_consumption: mode.energy_consumption || null,
        preferred: mode.preferred || false
      })))
      .select()

    if (error) {
      throw new Error(`Failed to create pattern task modes: ${error.message}`)
    }

    return data || []
  }

  /**
   * Copy task modes from one task to another
   */
  async copyTaskModes(sourceTaskId: string, targetTaskId: string): Promise<OptimizedTaskMode[]> {
    // Get source task modes
    const { data: sourceModes, error: sourceError } = await supabase
      .from('optimized_task_modes')
      .select('machine_id, processing_time, setup_time, cost_per_hour, energy_consumption, preferred')
      .eq('optimized_task_id', sourceTaskId)

    if (sourceError) {
      throw new Error(`Failed to get source task modes: ${sourceError.message}`)
    }

    if (!sourceModes || sourceModes.length === 0) {
      return []
    }

    // Create new task modes for target task
    const newTaskModes = sourceModes.map(mode => ({
      optimized_task_id: targetTaskId,
      machine_id: mode.machine_id,
      processing_time: mode.processing_time,
      setup_time: mode.setup_time,
      cost_per_hour: mode.cost_per_hour,
      energy_consumption: mode.energy_consumption || null,
      preferred: mode.preferred
    }))

    const { data, error } = await supabase
      .from('optimized_task_modes')
      .insert(newTaskModes)
      .select()

    if (error) {
      throw new Error(`Failed to copy task modes: ${error.message}`)
    }

    return data || []
  }

  /**
   * Get optimal machine for a task based on criteria
   */
  async getOptimalMachine(
    taskId: string, 
    criteria: {
      prioritize: 'cost' | 'time' | 'energy' | 'preferred'
      excludeMachines?: string[]
    } = { prioritize: 'cost' }
  ): Promise<MachineTaskMode | null> {
    
    const taskModes = await this.getTaskModes(taskId)
    
    if (taskModes.length === 0) {
      return null
    }

    // Filter out excluded machines
    let availableModes = taskModes.filter(mode => 
      mode.available && 
      !criteria.excludeMachines?.includes(mode.machine_id)
    )

    if (availableModes.length === 0) {
      return null
    }

    // Sort based on criteria
    switch (criteria.prioritize) {
      case 'preferred':
        availableModes.sort((a, b) => {
          if (a.preferred !== b.preferred) {
            return b.preferred ? 1 : -1
          }
          return a.cost_per_hour - b.cost_per_hour
        })
        break
      
      case 'time':
        availableModes.sort((a, b) => 
          (a.processing_time + a.setup_time) - (b.processing_time + b.setup_time)
        )
        break
      
      case 'energy':
        availableModes.sort((a, b) => 
          (a.energy_consumption || 0) - (b.energy_consumption || 0)
        )
        break
      
      case 'cost':
      default:
        availableModes.sort((a, b) => a.cost_per_hour - b.cost_per_hour)
        break
    }

    return availableModes[0]
  }

  /**
   * Validate task modes for constraint generation
   */
  async validatePatternTaskModes(patternId: string): Promise<{
    valid: boolean
    errors: string[]
    warnings: string[]
  }> {
    const errors: string[] = []
    const warnings: string[] = []

    // Get all tasks for the pattern
    const { data: tasks, error: tasksError } = await supabase
      .from('optimized_tasks')
      .select('id, name')
      .eq('pattern_id', patternId)

    if (tasksError) {
      errors.push(`Failed to get pattern tasks: ${tasksError.message}`)
      return { valid: false, errors, warnings }
    }

    if (!tasks || tasks.length === 0) {
      errors.push('Pattern has no tasks defined')
      return { valid: false, errors, warnings }
    }

    // Check each task has at least one valid mode
    const taskModeMap = await this.getPatternTaskModes(patternId)

    for (const task of tasks) {
      const modes = taskModeMap.get(task.id) || []
      
      if (modes.length === 0) {
        errors.push(`Task "${task.name}" has no machine modes defined`)
      } else {
        const availableModes = modes.filter(m => m.available)
        if (availableModes.length === 0) {
          errors.push(`Task "${task.name}" has no available machine modes`)
        } else if (availableModes.length === 1) {
          warnings.push(`Task "${task.name}" has only one available machine mode`)
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    }
  }

  /**
   * Get task mode statistics for performance analysis
   */
  async getTaskModeStatistics(patternId: string): Promise<{
    total_modes: number
    tasks_with_multiple_modes: number
    preferred_mode_coverage: number
    avg_modes_per_task: number
    cost_range: { min: number; max: number; avg: number }
    time_range: { min: number; max: number; avg: number }
  }> {
    const { data, error } = await supabase
      .from('optimized_task_modes')
      .select(`
        *,
        optimized_tasks!inner (
          pattern_id
        )
      `)
      .eq('optimized_tasks.pattern_id', patternId)

    if (error) {
      throw new Error(`Failed to get task mode statistics: ${error.message}`)
    }

    const modes = data || []
    const taskModeCount = new Map<string, number>()
    let preferredCount = 0
    let totalCost = 0
    let totalTime = 0
    let minCost = Infinity
    let maxCost = -Infinity
    let minTime = Infinity
    let maxTime = -Infinity

    for (const mode of modes) {
      // Count modes per task
      const taskId = mode.optimized_task_id
      taskModeCount.set(taskId, (taskModeCount.get(taskId) || 0) + 1)
      
      // Count preferred modes
      if (mode.preferred) {
        preferredCount++
      }
      
      // Calculate cost statistics
      totalCost += mode.cost_per_hour
      minCost = Math.min(minCost, mode.cost_per_hour)
      maxCost = Math.max(maxCost, mode.cost_per_hour)
      
      // Calculate time statistics
      const totalTaskTime = mode.processing_time + mode.setup_time
      totalTime += totalTaskTime
      minTime = Math.min(minTime, totalTaskTime)
      maxTime = Math.max(maxTime, totalTaskTime)
    }

    const uniqueTasks = taskModeCount.size
    const tasksWithMultipleModes = Array.from(taskModeCount.values()).filter(count => count > 1).length

    return {
      total_modes: modes.length,
      tasks_with_multiple_modes: tasksWithMultipleModes,
      preferred_mode_coverage: modes.length > 0 ? (preferredCount / modes.length) * 100 : 0,
      avg_modes_per_task: uniqueTasks > 0 ? modes.length / uniqueTasks : 0,
      cost_range: {
        min: minCost === Infinity ? 0 : minCost,
        max: maxCost === -Infinity ? 0 : maxCost,
        avg: modes.length > 0 ? totalCost / modes.length : 0
      },
      time_range: {
        min: minTime === Infinity ? 0 : minTime,
        max: maxTime === -Infinity ? 0 : maxTime,
        avg: modes.length > 0 ? totalTime / modes.length : 0
      }
    }
  }
}

export const taskModeService = new TaskModeService()
