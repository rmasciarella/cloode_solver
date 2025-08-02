// Updated database types with missing solver tables
// Based on schema analysis - add these to your existing database.types.ts

export interface Database {
  public: {
    Tables: {
      // ... existing tables ...

      // CRITICAL MISSING TABLES FOR SOLVER FUNCTIONALITY

      optimized_task_modes: {
        Row: {
          id: string
          optimized_task_id: string
          machine_id: string
          processing_time: number
          setup_time: number
          cost_per_hour: number
          energy_consumption: number | null
          preferred: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          optimized_task_id: string
          machine_id: string
          processing_time: number
          setup_time: number
          cost_per_hour: number
          energy_consumption?: number | null
          preferred?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          optimized_task_id?: string
          machine_id?: string
          processing_time?: number
          setup_time?: number
          cost_per_hour?: number
          energy_consumption?: number | null
          preferred?: boolean
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "optimized_task_modes_optimized_task_id_fkey"
            columns: ["optimized_task_id"]
            isOneToOne: false
            referencedRelation: "optimized_tasks"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "optimized_task_modes_machine_id_fkey"
            columns: ["machine_id"]
            isOneToOne: false
            referencedRelation: "machines"
            referencedColumns: ["id"]
          }
        ]
      }

      solved_schedules: {
        Row: {
          id: string
          pattern_id: string
          solver_version: string
          objective_value: number
          makespan: number
          total_cost: number
          total_lateness: number
          machine_utilization: number
          solve_time_seconds: number
          status: 'optimal' | 'feasible' | 'infeasible' | 'timeout' | 'unknown'
          solver_log: string | null
          constraint_count: number | null
          variable_count: number | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          pattern_id: string
          solver_version: string
          objective_value: number
          makespan: number
          total_cost: number
          total_lateness: number
          machine_utilization: number
          solve_time_seconds: number
          status: 'optimal' | 'feasible' | 'infeasible' | 'timeout' | 'unknown'
          solver_log?: string | null
          constraint_count?: number | null
          variable_count?: number | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          pattern_id?: string
          solver_version?: string
          objective_value?: number
          makespan?: number
          total_cost?: number
          total_lateness?: number
          machine_utilization?: number
          solve_time_seconds?: number
          status?: 'optimal' | 'feasible' | 'infeasible' | 'timeout' | 'unknown'
          solver_log?: string | null
          constraint_count?: number | null
          variable_count?: number | null
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "solved_schedules_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "optimized_patterns"
            referencedColumns: ["id"]
          }
        ]
      }

      scheduled_tasks: {
        Row: {
          id: string
          solved_schedule_id: string
          job_instance_id: string
          optimized_task_id: string
          assigned_machine_id: string
          assigned_operator_id: string | null
          start_time: number
          end_time: number
          processing_time: number
          setup_time: number
          actual_cost: number
          sequence_position: number | null
          priority: number | null
          created_at: string
        }
        Insert: {
          id?: string
          solved_schedule_id: string
          job_instance_id: string
          optimized_task_id: string
          assigned_machine_id: string
          assigned_operator_id?: string | null
          start_time: number
          end_time: number
          processing_time: number
          setup_time: number
          actual_cost: number
          sequence_position?: number | null
          priority?: number | null
          created_at?: string
        }
        Update: {
          id?: string
          solved_schedule_id?: string
          job_instance_id?: string
          optimized_task_id?: string
          assigned_machine_id?: string
          assigned_operator_id?: string | null
          start_time?: number
          end_time?: number
          processing_time?: number
          setup_time?: number
          actual_cost?: number
          sequence_position?: number | null
          priority?: number | null
          created_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "scheduled_tasks_solved_schedule_id_fkey"
            columns: ["solved_schedule_id"]
            isOneToOne: false
            referencedRelation: "solved_schedules"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "scheduled_tasks_job_instance_id_fkey"
            columns: ["job_instance_id"]
            isOneToOne: false
            referencedRelation: "job_instances"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "scheduled_tasks_optimized_task_id_fkey"
            columns: ["optimized_task_id"]
            isOneToOne: false
            referencedRelation: "optimized_tasks"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "scheduled_tasks_assigned_machine_id_fkey"
            columns: ["assigned_machine_id"]
            isOneToOne: false
            referencedRelation: "machines"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "scheduled_tasks_assigned_operator_id_fkey"
            columns: ["assigned_operator_id"]
            isOneToOne: false
            referencedRelation: "operators"
            referencedColumns: ["id"]
          }
        ]
      }

      sequence_reservations: {
        Row: {
          id: string
          machine_id: string
          start_time: number
          end_time: number
          reserved_by: 'opto' | 'bat' | 'maintenance' | 'setup'
          job_instance_id: string | null
          description: string | null
          priority: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          machine_id: string
          start_time: number
          end_time: number
          reserved_by: 'opto' | 'bat' | 'maintenance' | 'setup'
          job_instance_id?: string | null
          description?: string | null
          priority?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          machine_id?: string
          start_time?: number
          end_time?: number
          reserved_by?: 'opto' | 'bat' | 'maintenance' | 'setup'
          job_instance_id?: string | null
          description?: string | null
          priority?: number
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "sequence_reservations_machine_id_fkey"
            columns: ["machine_id"]
            isOneToOne: false
            referencedRelation: "machines"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "sequence_reservations_job_instance_id_fkey"
            columns: ["job_instance_id"]
            isOneToOne: false
            referencedRelation: "job_instances"
            referencedColumns: ["id"]
          }
        ]
      }

      // PERFORMANCE TRACKING TABLES

      solver_benchmarks: {
        Row: {
          id: string
          pattern_id: string
          instance_count: number
          legacy_solve_time: number | null
          optimized_solve_time: number
          performance_ratio: number | null
          memory_usage_mb: number | null
          constraint_count: number
          variable_count: number
          solver_version: string
          benchmark_date: string
          created_at: string
        }
        Insert: {
          id?: string
          pattern_id: string
          instance_count: number
          legacy_solve_time?: number | null
          optimized_solve_time: number
          performance_ratio?: number | null
          memory_usage_mb?: number | null
          constraint_count: number
          variable_count: number
          solver_version: string
          benchmark_date?: string
          created_at?: string
        }
        Update: {
          id?: string
          pattern_id?: string
          instance_count?: number
          legacy_solve_time?: number | null
          optimized_solve_time?: number
          performance_ratio?: number | null
          memory_usage_mb?: number | null
          constraint_count?: number
          variable_count?: number
          solver_version?: string
          benchmark_date?: string
          created_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "solver_benchmarks_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "optimized_patterns"
            referencedColumns: ["id"]
          }
        ]
      }

      // MULTI-OBJECTIVE OPTIMIZATION SUPPORT

      objective_configurations: {
        Row: {
          id: string
          pattern_id: string
          strategy: 'lexicographical' | 'weighted_sum' | 'epsilon_constraint' | 'pareto'
          primary_objective: 'makespan' | 'total_cost' | 'total_lateness' | 'machine_utilization'
          secondary_objective: 'makespan' | 'total_cost' | 'total_lateness' | 'machine_utilization' | null
          tertiary_objective: 'makespan' | 'total_cost' | 'total_lateness' | 'machine_utilization' | null
          weight_makespan: number | null
          weight_cost: number | null
          weight_lateness: number | null
          weight_utilization: number | null
          epsilon_makespan: number | null
          epsilon_cost: number | null
          epsilon_lateness: number | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          pattern_id: string
          strategy: 'lexicographical' | 'weighted_sum' | 'epsilon_constraint' | 'pareto'
          primary_objective: 'makespan' | 'total_cost' | 'total_lateness' | 'machine_utilization'
          secondary_objective?: 'makespan' | 'total_cost' | 'total_lateness' | 'machine_utilization' | null
          tertiary_objective?: 'makespan' | 'total_cost' | 'total_lateness' | 'machine_utilization' | null
          weight_makespan?: number | null
          weight_cost?: number | null
          weight_lateness?: number | null
          weight_utilization?: number | null
          epsilon_makespan?: number | null
          epsilon_cost?: number | null
          epsilon_lateness?: number | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          pattern_id?: string
          strategy?: 'lexicographical' | 'weighted_sum' | 'epsilon_constraint' | 'pareto'
          primary_objective?: 'makespan' | 'total_cost' | 'total_lateness' | 'machine_utilization'
          secondary_objective?: 'makespan' | 'total_cost' | 'total_lateness' | 'machine_utilization' | null
          tertiary_objective?: 'makespan' | 'total_cost' | 'total_lateness' | 'machine_utilization' | null
          weight_makespan?: number | null
          weight_cost?: number | null
          weight_lateness?: number | null
          weight_utilization?: number | null
          epsilon_makespan?: number | null
          epsilon_cost?: number | null
          epsilon_lateness?: number | null
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "objective_configurations_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: true
            referencedRelation: "optimized_patterns"
            referencedColumns: ["id"]
          }
        ]
      }
    }

    Views: {
      // PERFORMANCE VIEWS
      template_performance_metrics: {
        Row: {
          pattern_id: string
          pattern_name: string
          total_instances: number
          avg_solve_time: number
          avg_makespan: number
          avg_utilization: number
          avg_cost: number
          best_solve_time: number
          worst_solve_time: number
          performance_trend: 'improving' | 'stable' | 'degrading'
        }
      }

      solver_performance_summary: {
        Row: {
          solver_version: string
          total_problems_solved: number
          avg_performance_ratio: number
          total_time_saved: number
          problems_by_status: Record<string, number>
          constraint_complexity_avg: number
          memory_efficiency: number
        }
      }

      machine_utilization_metrics: {
        Row: {
          machine_id: string
          machine_name: string
          total_scheduled_time: number
          total_available_time: number
          utilization_rate: number
          avg_task_duration: number
          setup_time_ratio: number
          reservation_conflicts: number
        }
      }
    }

    Functions: {
      // SOLVER UTILITY FUNCTIONS
      get_machine_modes_for_task: {
        Args: { task_id: string }
        Returns: {
          machine_id: string
          machine_name: string
          processing_time: number
          setup_time: number
          cost_per_hour: number
          preferred: boolean
        }[]
      }

      get_schedule_solution: {
        Args: { 
          pattern_id: string
          schedule_id?: string 
        }
        Returns: {
          schedule: Database['public']['Tables']['solved_schedules']['Row']
          tasks: Database['public']['Tables']['scheduled_tasks']['Row'][]
          performance: Database['public']['Views']['template_performance_metrics']['Row']
        }
      }

      calculate_performance_metrics: {
        Args: { pattern_id: string }
        Returns: {
          avg_solve_time: number
          performance_improvement: number
          solution_quality: number
          resource_utilization: number
        }
      }
    }

    Enums: {
      solver_status: 'optimal' | 'feasible' | 'infeasible' | 'timeout' | 'unknown'
      reservation_type: 'opto' | 'bat' | 'maintenance' | 'setup'
      optimization_strategy: 'lexicographical' | 'weighted_sum' | 'epsilon_constraint' | 'pareto'
      objective_type: 'makespan' | 'total_cost' | 'total_lateness' | 'machine_utilization'
    }
  }
}

// HELPER TYPES FOR SOLVER INTEGRATION

export type OptimizedTaskMode = Database['public']['Tables']['optimized_task_modes']['Row']
export type SolvedSchedule = Database['public']['Tables']['solved_schedules']['Row']
export type ScheduledTask = Database['public']['Tables']['scheduled_tasks']['Row']
export type SequenceReservation = Database['public']['Tables']['sequence_reservations']['Row']
export type SolverBenchmark = Database['public']['Tables']['solver_benchmarks']['Row']
export type ObjectiveConfiguration = Database['public']['Tables']['objective_configurations']['Row']

export type SolverStatus = Database['public']['Enums']['solver_status']
export type ReservationType = Database['public']['Enums']['reservation_type']
export type OptimizationStrategy = Database['public']['Enums']['optimization_strategy']
export type ObjectiveType = Database['public']['Enums']['objective_type']

// COMPLEX QUERY TYPES

export interface ScheduleSolutionResponse {
  schedule: SolvedSchedule
  tasks: ScheduledTask[]
  reservations: SequenceReservation[]
  performance: Database['public']['Views']['template_performance_metrics']['Row']
}

export interface MachineTaskMode {
  machine_id: string
  machine_name: string
  processing_time: number
  setup_time: number
  cost_per_hour: number
  energy_consumption?: number
  preferred: boolean
  available: boolean
}

export interface SolverPerformanceMetrics {
  solve_time_seconds: number
  constraint_count: number
  variable_count: number
  memory_usage_mb: number
  performance_ratio: number
  solution_quality: 'optimal' | 'good' | 'acceptable' | 'poor'
}
