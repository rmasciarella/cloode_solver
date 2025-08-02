import { createBrowserClient } from '@supabase/ssr'
import { Database, SolvedSchedule, ScheduledTask, ScheduleSolutionResponse, SolverPerformanceMetrics } from '../database.types'

const supabase = createBrowserClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export class ScheduleSolutionService {
  
  /**
   * Store a complete solver solution with all scheduled tasks
   */
  async storeSolution(solution: {
    pattern_id: string
    solver_version: string
    objective_value: number
    makespan: number
    total_cost: number
    total_lateness: number
    machine_utilization: number
    solve_time_seconds: number
    status: 'optimal' | 'feasible' | 'infeasible' | 'timeout' | 'unknown'
    solver_log?: string
    constraint_count?: number
    variable_count?: number
    scheduled_tasks: Array<{
      job_instance_id: string
      optimized_task_id: string
      assigned_machine_id: string
      assigned_operator_id?: string
      start_time: number
      end_time: number
      processing_time: number
      setup_time: number
      actual_cost: number
      sequence_position?: number
      priority?: number
    }>
  }): Promise<{ schedule: SolvedSchedule; tasks: ScheduledTask[] }> {
    
    // Start transaction
    const { data: schedule, error: scheduleError } = await supabase
      .from('solved_schedules')
      .insert({
        pattern_id: solution.pattern_id,
        solver_version: solution.solver_version,
        objective_value: solution.objective_value,
        makespan: solution.makespan,
        total_cost: solution.total_cost,
        total_lateness: solution.total_lateness,
        machine_utilization: solution.machine_utilization,
        solve_time_seconds: solution.solve_time_seconds,
        status: solution.status,
        solver_log: solution.solver_log,
        constraint_count: solution.constraint_count,
        variable_count: solution.variable_count
      })
      .select()
      .single()

    if (scheduleError) {
      throw new Error(`Failed to store schedule: ${scheduleError.message}`)
    }

    // Store all scheduled tasks
    const tasksToInsert = solution.scheduled_tasks.map(task => ({
      ...task,
      solved_schedule_id: schedule.id
    }))

    const { data: tasks, error: tasksError } = await supabase
      .from('scheduled_tasks')
      .insert(tasksToInsert)
      .select()

    if (tasksError) {
      // Rollback schedule if tasks fail
      await supabase.from('solved_schedules').delete().eq('id', schedule.id)
      throw new Error(`Failed to store scheduled tasks: ${tasksError.message}`)
    }

    return { schedule, tasks: tasks || [] }
  }

  /**
   * Get the latest solution for a pattern
   */
  async getLatestSolution(patternId: string): Promise<ScheduleSolutionResponse | null> {
    const { data: schedule, error: scheduleError } = await supabase
      .from('solved_schedules')
      .select(`
        *,
        scheduled_tasks (
          id,
          job_instance_id,
          optimized_task_id,
          assigned_machine_id,
          assigned_operator_id,
          start_time,
          end_time,
          processing_time,
          setup_time,
          actual_cost,
          sequence_position,
          priority,
          created_at
        )
      `)
      .eq('pattern_id', patternId)
      .order('created_at', { ascending: false })
      .limit(1)
      .single()

    if (scheduleError) {
      if (scheduleError.code === 'PGRST116') {
        return null // No solutions found
      }
      throw new Error(`Failed to get solution: ${scheduleError.message}`)
    }

    // Get sequence reservations for this solution
    const { data: reservations, error: reservationsError } = await supabase
      .from('sequence_reservations')
      .select('*')
      .in('job_instance_id', schedule.scheduled_tasks.map(t => t.job_instance_id))

    if (reservationsError) {
      console.warn('Failed to get sequence reservations:', reservationsError.message)
    }

    // Get performance metrics
    const { data: performance, error: performanceError } = await supabase
      .from('template_performance_metrics')
      .select('*')
      .eq('pattern_id', patternId)
      .single()

    if (performanceError) {
      console.warn('Failed to get performance metrics:', performanceError.message)
    }

    return {
      schedule,
      tasks: schedule.scheduled_tasks || [],
      reservations: reservations || [],
      performance: performance || null
    }
  }

  /**
   * Get all solutions for a pattern with pagination
   */
  async getSolutionHistory(
    patternId: string, 
    { limit = 20, offset = 0 }: { limit?: number; offset?: number } = {}
  ): Promise<{ schedules: SolvedSchedule[]; total: number }> {
    
    const [schedulesResult, countResult] = await Promise.all([
      supabase
        .from('solved_schedules')
        .select('*')
        .eq('pattern_id', patternId)
        .order('created_at', { ascending: false })
        .range(offset, offset + limit - 1),
      
      supabase
        .from('solved_schedules')
        .select('*', { count: 'exact', head: true })
        .eq('pattern_id', patternId)
    ])

    if (schedulesResult.error) {
      throw new Error(`Failed to get solution history: ${schedulesResult.error.message}`)
    }

    if (countResult.error) {
      throw new Error(`Failed to get solution count: ${countResult.error.message}`)
    }

    return {
      schedules: schedulesResult.data || [],
      total: countResult.count || 0
    }
  }

  /**
   * Get detailed solution by schedule ID
   */
  async getSolutionDetails(scheduleId: string): Promise<ScheduleSolutionResponse | null> {
    const { data: schedule, error } = await supabase
      .from('solved_schedules')
      .select(`
        *,
        scheduled_tasks (
          *,
          job_instances!inner (
            id,
            pattern_id,
            instance_number,
            priority,
            due_date
          ),
          optimized_tasks!inner (
            id,
            name,
            description,
            pattern_id
          ),
          machines!inner (
            id,
            name,
            work_cell_id
          ),
          operators (
            id,
            name,
            shift_start,
            shift_end
          )
        )
      `)
      .eq('id', scheduleId)
      .single()

    if (error) {
      if (error.code === 'PGRST116') {
        return null
      }
      throw new Error(`Failed to get solution details: ${error.message}`)
    }

    // Get sequence reservations
    const taskJobInstanceIds = schedule.scheduled_tasks?.map(t => t.job_instances.id) || []
    const { data: reservations } = await supabase
      .from('sequence_reservations')
      .select('*')
      .in('job_instance_id', taskJobInstanceIds)

    // Get performance metrics
    const { data: performance } = await supabase
      .from('template_performance_metrics')
      .select('*')
      .eq('pattern_id', schedule.pattern_id)
      .single()

    return {
      schedule,
      tasks: schedule.scheduled_tasks || [],
      reservations: reservations || [],
      performance: performance || null
    }
  }

  /**
   * Compare two solutions
   */
  async compareSolutions(scheduleId1: string, scheduleId2: string): Promise<{
    schedule1: SolvedSchedule
    schedule2: SolvedSchedule
    comparison: {
      makespan_improvement: number
      cost_improvement: number
      lateness_improvement: number
      utilization_improvement: number
      solve_time_difference: number
      quality_comparison: 'better' | 'worse' | 'similar'
    }
  }> {
    const [result1, result2] = await Promise.all([
      supabase.from('solved_schedules').select('*').eq('id', scheduleId1).single(),
      supabase.from('solved_schedules').select('*').eq('id', scheduleId2).single()
    ])

    if (result1.error || result2.error) {
      throw new Error('Failed to get schedules for comparison')
    }

    const schedule1 = result1.data
    const schedule2 = result2.data

    const comparison = {
      makespan_improvement: ((schedule1.makespan - schedule2.makespan) / schedule1.makespan) * 100,
      cost_improvement: ((schedule1.total_cost - schedule2.total_cost) / schedule1.total_cost) * 100,
      lateness_improvement: ((schedule1.total_lateness - schedule2.total_lateness) / Math.max(schedule1.total_lateness, 1)) * 100,
      utilization_improvement: schedule2.machine_utilization - schedule1.machine_utilization,
      solve_time_difference: schedule2.solve_time_seconds - schedule1.solve_time_seconds,
      quality_comparison: this.compareQuality(schedule1, schedule2)
    }

    return { schedule1, schedule2, comparison }
  }

  /**
   * Get solver performance metrics for a pattern
   */
  async getPerformanceMetrics(patternId: string): Promise<SolverPerformanceMetrics | null> {
    const { data: metrics, error } = await supabase
      .from('solver_benchmarks')
      .select('*')
      .eq('pattern_id', patternId)
      .order('created_at', { ascending: false })
      .limit(1)
      .single()

    if (error) {
      if (error.code === 'PGRST116') {
        return null
      }
      throw new Error(`Failed to get performance metrics: ${error.message}`)
    }

    return {
      solve_time_seconds: metrics.optimized_solve_time,
      constraint_count: metrics.constraint_count,
      variable_count: metrics.variable_count,
      memory_usage_mb: metrics.memory_usage_mb || 0,
      performance_ratio: metrics.performance_ratio || 1,
      solution_quality: this.calculateSolutionQuality(metrics.performance_ratio || 1)
    }
  }

  /**
   * Delete old solutions (cleanup)
   */
  async cleanupOldSolutions(patternId: string, keepLatest: number = 10): Promise<number> {
    // Get IDs of solutions to keep
    const { data: keepSolutions, error: keepError } = await supabase
      .from('solved_schedules')
      .select('id')
      .eq('pattern_id', patternId)
      .order('created_at', { ascending: false })
      .limit(keepLatest)

    if (keepError) {
      throw new Error(`Failed to identify solutions to keep: ${keepError.message}`)
    }

    const keepIds = keepSolutions?.map(s => s.id) || []

    // Delete old solutions
    const { data: deletedSchedules, error: deleteError } = await supabase
      .from('solved_schedules')
      .delete()
      .eq('pattern_id', patternId)
      .not('id', 'in', `(${keepIds.join(',')})`)
      .select('id')

    if (deleteError) {
      throw new Error(`Failed to cleanup old solutions: ${deleteError.message}`)
    }

    return deletedSchedules?.length || 0
  }

  // Private helper methods

  private compareQuality(schedule1: SolvedSchedule, schedule2: SolvedSchedule): 'better' | 'worse' | 'similar' {
    // Multi-criteria comparison
    const score1 = this.calculateOverallScore(schedule1)
    const score2 = this.calculateOverallScore(schedule2)
    
    const improvement = (score2 - score1) / score1
    
    if (improvement > 0.05) return 'better'
    if (improvement < -0.05) return 'worse'
    return 'similar'
  }

  private calculateOverallScore(schedule: SolvedSchedule): number {
    // Weighted score: lower is better for makespan, cost, lateness; higher is better for utilization
    return (
      -(schedule.makespan * 0.3) +
      -(schedule.total_cost * 0.25) +
      -(schedule.total_lateness * 0.25) +
      (schedule.machine_utilization * 0.2)
    )
  }

  private calculateSolutionQuality(performanceRatio: number): 'optimal' | 'good' | 'acceptable' | 'poor' {
    if (performanceRatio >= 5) return 'optimal'
    if (performanceRatio >= 3) return 'good'
    if (performanceRatio >= 1.5) return 'acceptable'
    return 'poor'
  }
}

export const scheduleSolutionService = new ScheduleSolutionService()
