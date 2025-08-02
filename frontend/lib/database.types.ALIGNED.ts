export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  graphql_public: {
    Tables: {
      [_ in never]: never
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      graphql: {
        Args: {
          extensions?: Json
          operationName?: string
          query?: string
          variables?: Json
        }
        Returns: Json
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
  public: {
    Tables: {
      business_calendars: {
        Row: {
          calendar_id: string
          created_at: string | null
          default_end_time: number | null
          default_start_time: number | null
          description: string | null
          is_active: boolean | null
          is_default: boolean | null
          name: string
          timezone: string | null
          working_days_mask: number | null
        }
        Insert: {
          calendar_id?: string
          created_at?: string | null
          default_end_time?: number | null
          default_start_time?: number | null
          description?: string | null
          is_active?: boolean | null
          is_default?: boolean | null
          name: string
          timezone?: string | null
          working_days_mask?: number | null
        }
        Update: {
          calendar_id?: string
          created_at?: string | null
          default_end_time?: number | null
          default_start_time?: number | null
          description?: string | null
          is_active?: boolean | null
          is_default?: boolean | null
          name?: string
          timezone?: string | null
          working_days_mask?: number | null
        }
        Relationships: []
      }
      departments: {
        Row: {
          code: string
          cost_center: string | null
          created_at: string | null
          default_shift_end: number | null
          default_shift_start: number | null
          department_id: string
          description: string | null
          is_active: boolean | null
          name: string
          overtime_allowed: boolean | null
          parent_department_id: string | null
          updated_at: string | null
        }
        Insert: {
          code: string
          cost_center?: string | null
          created_at?: string | null
          default_shift_end?: number | null
          default_shift_start?: number | null
          department_id?: string
          description?: string | null
          is_active?: boolean | null
          name: string
          overtime_allowed?: boolean | null
          parent_department_id?: string | null
          updated_at?: string | null
        }
        Update: {
          code?: string
          cost_center?: string | null
          created_at?: string | null
          default_shift_end?: number | null
          default_shift_start?: number | null
          department_id?: string
          description?: string | null
          is_active?: boolean | null
          name?: string
          overtime_allowed?: boolean | null
          parent_department_id?: string | null
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "departments_parent_department_id_fkey"
            columns: ["parent_department_id"]
            isOneToOne: false
            referencedRelation: "departments"
            referencedColumns: ["department_id"]
          },
        ]
      }
      job_instances: {
        Row: {
          actual_cost: number | null
          actual_duration_hours: number | null
          batch_id: string | null
          created_at: string | null
          customer_order_id: string | null
          department_id: string | null
          description: string | null
          due_date: string | null
          earliest_start_date: string | null
          estimated_cost: number | null
          estimated_duration_hours: number | null
          instance_id: string
          name: string
          pattern_id: string | null
          priority: number | null
          quantity: number | null
          revenue_value: number | null
          status: string | null
          template_id: string | null
          updated_at: string | null
        }
        Insert: {
          actual_cost?: number | null
          actual_duration_hours?: number | null
          batch_id?: string | null
          created_at?: string | null
          customer_order_id?: string | null
          department_id?: string | null
          description?: string | null
          due_date?: string | null
          earliest_start_date?: string | null
          estimated_cost?: number | null
          estimated_duration_hours?: number | null
          instance_id?: string
          name: string
          pattern_id?: string | null
          priority?: number | null
          quantity?: number | null
          revenue_value?: number | null
          status?: string | null
          template_id?: string | null
          updated_at?: string | null
        }
        Update: {
          actual_cost?: number | null
          actual_duration_hours?: number | null
          batch_id?: string | null
          created_at?: string | null
          customer_order_id?: string | null
          department_id?: string | null
          description?: string | null
          due_date?: string | null
          earliest_start_date?: string | null
          estimated_cost?: number | null
          estimated_duration_hours?: number | null
          instance_id?: string
          name?: string
          pattern_id?: string | null
          priority?: number | null
          quantity?: number | null
          revenue_value?: number | null
          status?: string | null
          template_id?: string | null
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "job_instances_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "constraint_generation_stats"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "job_instances_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "job_optimized_patterns"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "job_instances_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "template_performance_summary"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "job_instances_template_id_fkey"
            columns: ["template_id"]
            isOneToOne: false
            referencedRelation: "constraint_generation_stats"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "job_instances_template_id_fkey"
            columns: ["template_id"]
            isOneToOne: false
            referencedRelation: "job_optimized_patterns"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "job_instances_template_id_fkey"
            columns: ["template_id"]
            isOneToOne: false
            referencedRelation: "template_performance_summary"
            referencedColumns: ["pattern_id"]
          },
        ]
      }
      job_optimized_patterns: {
        Row: {
          baseline_performance_seconds: number | null
          created_at: string | null
          critical_path_length_minutes: number | null
          description: string | null
          is_active: boolean | null
          is_blessed: boolean | null
          last_benchmarked_at: string | null
          name: string
          optimization_techniques_applied: string[] | null
          optimized_performance_seconds: number | null
          pattern_id: string
          performance_target_seconds: number | null
          redundant_constraints_count: number | null
          solver_parameters: Json | null
          speedup_factor: number | null
          symmetry_breaking_enabled: boolean | null
          task_count: number | null
          total_min_duration_minutes: number | null
          updated_at: string | null
        }
        Insert: {
          baseline_performance_seconds?: number | null
          created_at?: string | null
          critical_path_length_minutes?: number | null
          description?: string | null
          is_active?: boolean | null
          is_blessed?: boolean | null
          last_benchmarked_at?: string | null
          name: string
          optimization_techniques_applied?: string[] | null
          optimized_performance_seconds?: number | null
          pattern_id?: string
          performance_target_seconds?: number | null
          redundant_constraints_count?: number | null
          solver_parameters?: Json | null
          speedup_factor?: number | null
          symmetry_breaking_enabled?: boolean | null
          task_count?: number | null
          total_min_duration_minutes?: number | null
          updated_at?: string | null
        }
        Update: {
          baseline_performance_seconds?: number | null
          created_at?: string | null
          critical_path_length_minutes?: number | null
          description?: string | null
          is_active?: boolean | null
          is_blessed?: boolean | null
          last_benchmarked_at?: string | null
          name?: string
          optimization_techniques_applied?: string[] | null
          optimized_performance_seconds?: number | null
          pattern_id?: string
          performance_target_seconds?: number | null
          redundant_constraints_count?: number | null
          solver_parameters?: Json | null
          speedup_factor?: number | null
          symmetry_breaking_enabled?: boolean | null
          task_count?: number | null
          total_min_duration_minutes?: number | null
          updated_at?: string | null
        }
        Relationships: []
      }
      machines: {
        Row: {
          average_utilization_percent: number | null
          calendar_id: string | null
          capacity: number | null
          cell_id: string
          cost_per_hour: number | null
          created_at: string | null
          department_id: string | null
          efficiency_rating: number | null
          is_active: boolean | null
          last_maintenance_date: string | null
          machine_resource_id: string
          machine_type: string | null
          maintenance_interval_hours: number | null
          maintenance_window_end: number | null
          maintenance_window_start: number | null
          manufacturer: string | null
          model: string | null
          name: string
          next_maintenance_due: string | null
          setup_time_minutes: number | null
          teardown_time_minutes: number | null
          uptime_target_percent: number | null
          year_installed: number | null
        }
        Insert: {
          average_utilization_percent?: number | null
          calendar_id?: string | null
          capacity?: number | null
          cell_id: string
          cost_per_hour?: number | null
          created_at?: string | null
          department_id?: string | null
          efficiency_rating?: number | null
          is_active?: boolean | null
          last_maintenance_date?: string | null
          machine_resource_id?: string
          machine_type?: string | null
          maintenance_interval_hours?: number | null
          maintenance_window_end?: number | null
          maintenance_window_start?: number | null
          manufacturer?: string | null
          model?: string | null
          name: string
          next_maintenance_due?: string | null
          setup_time_minutes?: number | null
          teardown_time_minutes?: number | null
          uptime_target_percent?: number | null
          year_installed?: number | null
        }
        Update: {
          average_utilization_percent?: number | null
          calendar_id?: string | null
          capacity?: number | null
          cell_id?: string
          cost_per_hour?: number | null
          created_at?: string | null
          department_id?: string | null
          efficiency_rating?: number | null
          is_active?: boolean | null
          last_maintenance_date?: string | null
          machine_resource_id?: string
          machine_type?: string | null
          maintenance_interval_hours?: number | null
          maintenance_window_end?: number | null
          maintenance_window_start?: number | null
          manufacturer?: string | null
          model?: string | null
          name?: string
          next_maintenance_due?: string | null
          setup_time_minutes?: number | null
          teardown_time_minutes?: number | null
          uptime_target_percent?: number | null
          year_installed?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "machines_calendar_id_fkey"
            columns: ["calendar_id"]
            isOneToOne: false
            referencedRelation: "business_calendars"
            referencedColumns: ["calendar_id"]
          },
          {
            foreignKeyName: "machines_cell_id_fkey"
            columns: ["cell_id"]
            isOneToOne: false
            referencedRelation: "work_cells"
            referencedColumns: ["cell_id"]
          },
          {
            foreignKeyName: "machines_department_id_fkey"
            columns: ["department_id"]
            isOneToOne: false
            referencedRelation: "departments"
            referencedColumns: ["department_id"]
          },
        ]
      }
      operators: {
        Row: {
          created_at: string | null
          department_id: string | null
          efficiency_rating: number | null
          employee_number: string | null
          employment_status: string | null
          hire_date: string | null
          hourly_rate: number | null
          is_active: boolean | null
          max_hours_per_day: number | null
          max_hours_per_week: number | null
          name: string
          operator_id: string
          overtime_rate_multiplier: number | null
          quality_score: number | null
          safety_score: number | null
        }
        Insert: {
          created_at?: string | null
          department_id?: string | null
          efficiency_rating?: number | null
          employee_number?: string | null
          employment_status?: string | null
          hire_date?: string | null
          hourly_rate?: number | null
          is_active?: boolean | null
          max_hours_per_day?: number | null
          max_hours_per_week?: number | null
          name: string
          operator_id?: string
          overtime_rate_multiplier?: number | null
          quality_score?: number | null
          safety_score?: number | null
        }
        Update: {
          created_at?: string | null
          department_id?: string | null
          efficiency_rating?: number | null
          employee_number?: string | null
          employment_status?: string | null
          hire_date?: string | null
          hourly_rate?: number | null
          is_active?: boolean | null
          max_hours_per_day?: number | null
          max_hours_per_week?: number | null
          name?: string
          operator_id?: string
          overtime_rate_multiplier?: number | null
          quality_score?: number | null
          safety_score?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "operators_department_id_fkey"
            columns: ["department_id"]
            isOneToOne: false
            referencedRelation: "departments"
            referencedColumns: ["department_id"]
          },
        ]
      }
      optimized_precedences: {
        Row: {
          created_at: string | null
          pattern_id: string
          precedence_id: string
          predecessor_task_id: string
          successor_task_id: string
        }
        Insert: {
          created_at?: string | null
          pattern_id: string
          precedence_id?: string
          predecessor_task_id: string
          successor_task_id: string
        }
        Update: {
          created_at?: string | null
          pattern_id?: string
          precedence_id?: string
          predecessor_task_id?: string
          successor_task_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "optimized_precedences_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "constraint_generation_stats"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "optimized_precedences_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "job_optimized_patterns"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "optimized_precedences_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "template_performance_summary"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "optimized_precedences_predecessor_task_id_fkey"
            columns: ["predecessor_task_id"]
            isOneToOne: false
            referencedRelation: "optimized_tasks"
            referencedColumns: ["optimized_task_id"]
          },
          {
            foreignKeyName: "optimized_precedences_successor_task_id_fkey"
            columns: ["successor_task_id"]
            isOneToOne: false
            referencedRelation: "optimized_tasks"
            referencedColumns: ["optimized_task_id"]
          },
        ]
      }
      optimized_task_modes: {
        Row: {
          created_at: string | null
          duration_minutes: number
          machine_resource_id: string
          optimized_task_id: string
          optimized_task_mode_id: string
        }
        Insert: {
          created_at?: string | null
          duration_minutes: number
          machine_resource_id: string
          optimized_task_id: string
          optimized_task_mode_id?: string
        }
        Update: {
          created_at?: string | null
          duration_minutes?: number
          machine_resource_id?: string
          optimized_task_id?: string
          optimized_task_mode_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "optimized_task_modes_machine_resource_id_fkey"
            columns: ["machine_resource_id"]
            isOneToOne: false
            referencedRelation: "machines"
            referencedColumns: ["machine_resource_id"]
          },
          {
            foreignKeyName: "optimized_task_modes_optimized_task_id_fkey"
            columns: ["optimized_task_id"]
            isOneToOne: false
            referencedRelation: "optimized_tasks"
            referencedColumns: ["optimized_task_id"]
          },
        ]
      }
      optimized_task_setup_times: {
        Row: {
          complexity_level: string | null
          created_at: string | null
          efficiency_impact_percent: number | null
          from_optimized_task_id: string
          machine_resource_id: string
          product_family_from: string | null
          product_family_to: string | null
          requires_certification: boolean | null
          requires_operator_skill: string | null
          requires_supervisor_approval: boolean | null
          setup_cost: number | null
          setup_time_id: string
          setup_time_minutes: number
          setup_type: string | null
          to_optimized_task_id: string
          updated_at: string | null
        }
        Insert: {
          complexity_level?: string | null
          created_at?: string | null
          efficiency_impact_percent?: number | null
          from_optimized_task_id: string
          machine_resource_id: string
          product_family_from?: string | null
          product_family_to?: string | null
          requires_certification?: boolean | null
          requires_operator_skill?: string | null
          requires_supervisor_approval?: boolean | null
          setup_cost?: number | null
          setup_time_id?: string
          setup_time_minutes: number
          setup_type?: string | null
          to_optimized_task_id: string
          updated_at?: string | null
        }
        Update: {
          complexity_level?: string | null
          created_at?: string | null
          efficiency_impact_percent?: number | null
          from_optimized_task_id?: string
          machine_resource_id?: string
          product_family_from?: string | null
          product_family_to?: string | null
          requires_certification?: boolean | null
          requires_operator_skill?: string | null
          requires_supervisor_approval?: boolean | null
          setup_cost?: number | null
          setup_time_id?: string
          setup_time_minutes?: number
          setup_type?: string | null
          to_optimized_task_id?: string
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "optimized_task_setup_times_from_optimized_task_id_fkey"
            columns: ["from_optimized_task_id"]
            isOneToOne: false
            referencedRelation: "optimized_tasks"
            referencedColumns: ["optimized_task_id"]
          },
          {
            foreignKeyName: "optimized_task_setup_times_machine_resource_id_fkey"
            columns: ["machine_resource_id"]
            isOneToOne: false
            referencedRelation: "machines"
            referencedColumns: ["machine_resource_id"]
          },
          {
            foreignKeyName: "optimized_task_setup_times_to_optimized_task_id_fkey"
            columns: ["to_optimized_task_id"]
            isOneToOne: false
            referencedRelation: "optimized_tasks"
            referencedColumns: ["optimized_task_id"]
          },
        ]
      }
      optimized_tasks: {
        Row: {
          created_at: string | null
          department_id: string | null
          is_setup: boolean | null
          is_unattended: boolean | null
          max_operators: number | null
          min_operators: number | null
          name: string
          operator_efficiency_curve: string | null
          optimized_task_id: string
          pattern_id: string
          position: number | null
          sequence_id: string | null
        }
        Insert: {
          created_at?: string | null
          department_id?: string | null
          is_setup?: boolean | null
          is_unattended?: boolean | null
          max_operators?: number | null
          min_operators?: number | null
          name: string
          operator_efficiency_curve?: string | null
          optimized_task_id?: string
          pattern_id: string
          position?: number | null
          sequence_id?: string | null
        }
        Update: {
          created_at?: string | null
          department_id?: string | null
          is_setup?: boolean | null
          is_unattended?: boolean | null
          max_operators?: number | null
          min_operators?: number | null
          name?: string
          operator_efficiency_curve?: string | null
          optimized_task_id?: string
          pattern_id?: string
          position?: number | null
          sequence_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "optimized_tasks_department_id_fkey"
            columns: ["department_id"]
            isOneToOne: false
            referencedRelation: "departments"
            referencedColumns: ["department_id"]
          },
          {
            foreignKeyName: "optimized_tasks_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "constraint_generation_stats"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "optimized_tasks_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "job_optimized_patterns"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "optimized_tasks_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "template_performance_summary"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "optimized_tasks_sequence_id_fkey"
            columns: ["sequence_id"]
            isOneToOne: false
            referencedRelation: "sequence_resources"
            referencedColumns: ["sequence_id"]
          },
        ]
      }
      scheduled_tasks: {
        Row: {
          assigned_machine_id: string
          created_at: string | null
          end_time_units: number
          instance_id: string
          optimized_task_id: string
          schedule_id: string
          scheduled_task_id: string
          start_time_units: number
        }
        Insert: {
          assigned_machine_id: string
          created_at?: string | null
          end_time_units: number
          instance_id: string
          optimized_task_id: string
          schedule_id: string
          scheduled_task_id?: string
          start_time_units: number
        }
        Update: {
          assigned_machine_id?: string
          created_at?: string | null
          end_time_units?: number
          instance_id?: string
          optimized_task_id?: string
          schedule_id?: string
          scheduled_task_id?: string
          start_time_units?: number
        }
        Relationships: [
          {
            foreignKeyName: "scheduled_tasks_assigned_machine_id_fkey"
            columns: ["assigned_machine_id"]
            isOneToOne: false
            referencedRelation: "machines"
            referencedColumns: ["machine_resource_id"]
          },
          {
            foreignKeyName: "scheduled_tasks_instance_id_fkey"
            columns: ["instance_id"]
            isOneToOne: false
            referencedRelation: "job_instances"
            referencedColumns: ["instance_id"]
          },
          {
            foreignKeyName: "scheduled_tasks_optimized_task_id_fkey"
            columns: ["optimized_task_id"]
            isOneToOne: false
            referencedRelation: "optimized_tasks"
            referencedColumns: ["optimized_task_id"]
          },
          {
            foreignKeyName: "scheduled_tasks_schedule_id_fkey"
            columns: ["schedule_id"]
            isOneToOne: false
            referencedRelation: "solved_schedules"
            referencedColumns: ["schedule_id"]
          },
        ]
      }
      sequence_reservations: {
        Row: {
          created_at: string | null
          instance_id: string
          reservation_end_time_units: number
          reservation_id: string
          reservation_start_time_units: number
          schedule_id: string
          sequence_id: string
        }
        Insert: {
          created_at?: string | null
          instance_id: string
          reservation_end_time_units: number
          reservation_id?: string
          reservation_start_time_units: number
          schedule_id: string
          sequence_id: string
        }
        Update: {
          created_at?: string | null
          instance_id?: string
          reservation_end_time_units?: number
          reservation_id?: string
          reservation_start_time_units?: number
          schedule_id?: string
          sequence_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "sequence_reservations_instance_id_fkey"
            columns: ["instance_id"]
            isOneToOne: false
            referencedRelation: "job_instances"
            referencedColumns: ["instance_id"]
          },
          {
            foreignKeyName: "sequence_reservations_schedule_id_fkey"
            columns: ["schedule_id"]
            isOneToOne: false
            referencedRelation: "solved_schedules"
            referencedColumns: ["schedule_id"]
          },
        ]
      }
      sequence_resources: {
        Row: {
          created_at: string | null
          department_id: string | null
          description: string | null
          is_active: boolean | null
          max_concurrent_jobs: number | null
          name: string
          priority: number | null
          resource_type: string | null
          sequence_id: string
          setup_time_minutes: number | null
          teardown_time_minutes: number | null
        }
        Insert: {
          created_at?: string | null
          department_id?: string | null
          description?: string | null
          is_active?: boolean | null
          max_concurrent_jobs?: number | null
          name: string
          priority?: number | null
          resource_type?: string | null
          sequence_id: string
          setup_time_minutes?: number | null
          teardown_time_minutes?: number | null
        }
        Update: {
          created_at?: string | null
          department_id?: string | null
          description?: string | null
          is_active?: boolean | null
          max_concurrent_jobs?: number | null
          name?: string
          priority?: number | null
          resource_type?: string | null
          sequence_id?: string
          setup_time_minutes?: number | null
          teardown_time_minutes?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "sequence_resources_department_id_fkey"
            columns: ["department_id"]
            isOneToOne: false
            referencedRelation: "departments"
            referencedColumns: ["department_id"]
          },
        ]
      }
      skills: {
        Row: {
          category: string | null
          certification_expires_after_months: number | null
          certification_required: boolean | null
          complexity_level: string | null
          created_at: string | null
          department_id: string | null
          description: string | null
          is_active: boolean | null
          market_hourly_rate: number | null
          name: string
          skill_id: string
          skill_scarcity_level: string | null
          training_hours_required: number | null
        }
        Insert: {
          category?: string | null
          certification_expires_after_months?: number | null
          certification_required?: boolean | null
          complexity_level?: string | null
          created_at?: string | null
          department_id?: string | null
          description?: string | null
          is_active?: boolean | null
          market_hourly_rate?: number | null
          name: string
          skill_id?: string
          skill_scarcity_level?: string | null
          training_hours_required?: number | null
        }
        Update: {
          category?: string | null
          certification_expires_after_months?: number | null
          certification_required?: boolean | null
          complexity_level?: string | null
          created_at?: string | null
          department_id?: string | null
          description?: string | null
          is_active?: boolean | null
          market_hourly_rate?: number | null
          name?: string
          skill_id?: string
          skill_scarcity_level?: string | null
          training_hours_required?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "skills_department_id_fkey"
            columns: ["department_id"]
            isOneToOne: false
            referencedRelation: "departments"
            referencedColumns: ["department_id"]
          },
        ]
      }
      solved_schedules: {
        Row: {
          created_at: string | null
          instance_count: number
          makespan_time_units: number | null
          maximum_lateness_minutes: number | null
          pattern_id: string
          schedule_id: string
          solution_timestamp: string | null
          solve_time_seconds: number
          solver_status: string
          speedup_vs_legacy: number | null
          total_lateness_minutes: number | null
        }
        Insert: {
          created_at?: string | null
          instance_count: number
          makespan_time_units?: number | null
          maximum_lateness_minutes?: number | null
          pattern_id: string
          schedule_id?: string
          solution_timestamp?: string | null
          solve_time_seconds: number
          solver_status: string
          speedup_vs_legacy?: number | null
          total_lateness_minutes?: number | null
        }
        Update: {
          created_at?: string | null
          instance_count?: number
          makespan_time_units?: number | null
          maximum_lateness_minutes?: number | null
          pattern_id?: string
          schedule_id?: string
          solution_timestamp?: string | null
          solve_time_seconds?: number
          solver_status?: string
          speedup_vs_legacy?: number | null
          total_lateness_minutes?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "solved_schedules_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "constraint_generation_stats"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "solved_schedules_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "job_optimized_patterns"
            referencedColumns: ["pattern_id"]
          },
          {
            foreignKeyName: "solved_schedules_pattern_id_fkey"
            columns: ["pattern_id"]
            isOneToOne: false
            referencedRelation: "template_performance_summary"
            referencedColumns: ["pattern_id"]
          },
        ]
      }
      work_cells: {
        Row: {
          average_throughput_per_hour: number | null
          calendar_id: string | null
          capacity: number | null
          cell_id: string
          cell_type: string | null
          created_at: string | null
          department_id: string | null
          floor_location: string | null
          flow_priority: number | null
          is_active: boolean | null
          name: string
          target_utilization: number | null
          wip_limit: number | null
        }
        Insert: {
          average_throughput_per_hour?: number | null
          calendar_id?: string | null
          capacity?: number | null
          cell_id?: string
          cell_type?: string | null
          created_at?: string | null
          department_id?: string | null
          floor_location?: string | null
          flow_priority?: number | null
          is_active?: boolean | null
          name: string
          target_utilization?: number | null
          wip_limit?: number | null
        }
        Update: {
          average_throughput_per_hour?: number | null
          calendar_id?: string | null
          capacity?: number | null
          cell_id?: string
          cell_type?: string | null
          created_at?: string | null
          department_id?: string | null
          floor_location?: string | null
          flow_priority?: number | null
          is_active?: boolean | null
          name?: string
          target_utilization?: number | null
          wip_limit?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "work_cells_calendar_id_fkey"
            columns: ["calendar_id"]
            isOneToOne: false
            referencedRelation: "business_calendars"
            referencedColumns: ["calendar_id"]
          },
          {
            foreignKeyName: "work_cells_department_id_fkey"
            columns: ["department_id"]
            isOneToOne: false
            referencedRelation: "departments"
            referencedColumns: ["department_id"]
          },
        ]
      }
    }
    Views: {
      constraint_generation_stats: {
        Row: {
          constraint_complexity: number | null
          mode_count: number | null
          name: string | null
          pattern_id: string | null
          precedence_count: number | null
          task_count: number | null
        }
        Relationships: []
      }
      template_performance_summary: {
        Row: {
          avg_solve_time: number | null
          avg_speedup_factor: number | null
          avg_total_lateness: number | null
          best_solve_time: number | null
          max_instances_solved: number | null
          pattern_id: string | null
          pattern_name: string | null
          solve_count: number | null
          total_instances_processed: number | null
          worst_solve_time: number | null
        }
        Relationships: []
      }
    }
    Functions: {
      load_pattern_for_solver: {
        Args: { p_pattern_id: string }
        Returns: {
          pattern_name: string
          solver_parameters: Json
          task_id: string
          task_name: string
          is_unattended: boolean
          sequence_id: string
          mode_id: string
          machine_id: string
          duration_minutes: number
          predecessor_task_id: string
          successor_task_id: string
        }[]
      }
      store_solved_schedule: {
        Args: {
          p_instance_count: number
          p_makespan_time_units: number
          p_pattern_id: string
          p_solve_time_seconds: number
          p_solver_status: string
          p_speedup_vs_legacy: number
          p_total_lateness_minutes: number
        }
        Returns: string
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  graphql_public: {
    Enums: {},
  },
  public: {
    Enums: {},
  },
} as const

