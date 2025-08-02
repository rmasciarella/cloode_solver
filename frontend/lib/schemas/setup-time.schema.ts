import { z } from 'zod'

export const setupTimeSchema = z.object({
  from_optimized_task_id: z.string().min(1, 'From task is required'),
  to_optimized_task_id: z.string().min(1, 'To task is required'),
  machine_resource_id: z.string().min(1, 'Machine is required'),
  setup_time_minutes: z.number().min(0, 'Setup time must be non-negative'),
  setup_type: z.string(),
  complexity_level: z.string(),
  requires_operator_skill: z.string().optional(),
  requires_certification: z.boolean(),
  requires_supervisor_approval: z.boolean(),
  setup_cost: z.number().min(0, 'Cost must be non-negative'),
  efficiency_impact_percent: z.number().min(0).max(100, 'Impact must be between 0 and 100%'),
  product_family_from: z.string().optional(),
  product_family_to: z.string().optional()
}).refine(
  (data) => data.from_optimized_task_id !== data.to_optimized_task_id,
  {
    message: "From and To tasks must be different",
    path: ["to_optimized_task_id"]
  }
)

export type SetupTimeFormData = z.infer<typeof setupTimeSchema>

export const setupTypes = [
  { value: 'standard', label: 'Standard' },
  { value: 'complex', label: 'Complex' },
  { value: 'tooling_change', label: 'Tooling Change' },
  { value: 'calibration', label: 'Calibration' },
  { value: 'cleaning', label: 'Cleaning' }
] as const

export const complexityLevels = [
  { value: 'simple', label: 'Simple' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'complex', label: 'Complex' },
  { value: 'expert_required', label: 'Expert Required' }
] as const

export const skillLevels = [
  { value: 'NOVICE', label: 'Novice' },
  { value: 'COMPETENT', label: 'Competent' },
  { value: 'PROFICIENT', label: 'Proficient' },
  { value: 'EXPERT', label: 'Expert' }
] as const