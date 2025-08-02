import { z } from 'zod'

// Custom JSON schema validator
const jsonSchema = z.string()
  .min(1, 'JSON is required')
  .refine((val) => {
    try {
      JSON.parse(val)
      return true
    } catch {
      return false
    }
  }, 'Must be valid JSON')
  .transform((val) => {
    try {
      return JSON.parse(val)
    } catch {
      throw new Error('Invalid JSON')
    }
  })

// Solver parameters schema - Complete OR-Tools CP-SAT parameters
const solverParametersSchema = z.object({
  // Search Parameters
  num_search_workers: z.number().int().min(0).max(16).optional(), // 0 = auto
  search_branching: z.enum(['AUTOMATIC_SEARCH', 'FIXED_SEARCH', 'PORTFOLIO_SEARCH', 'LP_SEARCH']).optional(),
  linearization_level: z.number().int().min(0).max(2).optional(),
  cp_model_probing_level: z.number().int().min(0).max(3).optional(),
  cp_model_presolve: z.boolean().optional(),
  repair_hint: z.boolean().optional(),
  hint_conflict_limit: z.number().int().min(0).optional(),
  log_search_progress: z.boolean().optional(),
  use_lp_lns: z.boolean().optional(),
  
  // Time Limits
  max_time_in_seconds: z.number().min(0).optional(),
  max_deterministic_time: z.number().min(0).optional(),
  max_preprocessing_time: z.number().min(0).optional(),
  
  // Solution Limits
  max_number_of_conflicts: z.number().int().min(0).optional(),
  stop_after_first_solution: z.boolean().optional(),
  max_memory_in_mb: z.number().int().min(0).optional(),
  
  // Optimization Parameters
  optimize_with_core: z.boolean().optional(),
  optimize_with_max_hs: z.boolean().optional(),
  mip_max_bound: z.number().optional(),
  relative_gap_limit: z.number().min(0).max(1).optional(),
  absolute_gap_limit: z.number().min(0).optional(),
  
  // Symmetry Breaking
  symmetry_level: z.number().int().min(0).max(2).optional(),
  max_symmetry_detection_time: z.number().min(0).optional(),
  
  // Restart Strategy
  use_fast_restart: z.boolean().optional(),
  restart_period: z.number().int().min(1).optional(),
  restart_running_window_size: z.number().int().min(1).optional(),
  
  // Variable/Value Selection
  preferred_variable_order: z.enum(['IN_ORDER', 'IN_REVERSE_ORDER', 'IN_RANDOM_ORDER']).optional(),
  initial_polarity: z.enum(['POLARITY_TRUE', 'POLARITY_FALSE', 'POLARITY_RANDOM']).optional(),
  minimization_algorithm: z.enum(['NONE', 'SIMPLE', 'ROTATION']).optional(),
  
  // Advanced Parameters
  use_probing_search: z.boolean().optional(),
  enumerate_all_solutions: z.boolean().optional(),
  keep_all_feasible_solutions_in_presolve: z.boolean().optional(),
  fill_additional_solutions_in_response: z.boolean().optional(),
  instantiate_all_variables: z.boolean().optional(),
  auto_detect_greater_than_at_least_one_of: z.boolean().optional(),
  
  // Clause Parameters
  clause_cleanup_period: z.number().int().min(1).optional(),
  clause_cleanup_ratio: z.number().min(0).max(1).optional(),
  max_clause_activity_value: z.number().min(0).optional(),
  
  // Random Seed
  random_seed: z.number().int().min(0).optional(),
  
  // Custom Application Parameters (not OR-Tools parameters)
  hash_pattern_id: z.number().optional(), // Application-specific parameter
  search_strategy: z.string().optional() // Legacy parameter, kept for compatibility
}).strict() // Prevent unknown properties

export const jobTemplateFormSchema = z.object({
  name: z.string()
    .min(1, 'Template name is required')
    .max(255, 'Name must be 255 characters or less'),
  description: z.string()
    .optional()
    .transform(val => val === '' ? undefined : val),
  solver_parameters: jsonSchema
    .pipe(solverParametersSchema),
  task_count: z.number()
    .int()
    .min(1, 'Must have at least 1 task')
    .max(1000, 'Task count cannot exceed 1000'),
  total_min_duration_minutes: z.number()
    .int()
    .min(0, 'Duration must be non-negative')
    .max(10080, 'Duration cannot exceed 1 week (10080 minutes)'),
  critical_path_length_minutes: z.number()
    .int()
    .min(0, 'Length must be non-negative')
    .max(10080, 'Length cannot exceed 1 week (10080 minutes)')
}).refine(data => data.critical_path_length_minutes <= data.total_min_duration_minutes, {
  message: 'Critical path length cannot exceed total duration',
  path: ['critical_path_length_minutes']
})

export type JobTemplateFormData = z.infer<typeof jobTemplateFormSchema>