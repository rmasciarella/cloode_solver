import { z } from 'zod'

export const sequenceResourceFormSchema = z.object({
  name: z.string()
    .min(1, 'Resource name is required')
    .max(255, 'Name must be 255 characters or less'),
  code: z.string()
    .min(1, 'Resource code is required')
    .max(50, 'Code must be 50 characters or less')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Code can only contain letters, numbers, underscores, and hyphens'),
  resource_type: z.string()
    .min(1, 'Resource type is required'),
  department_id: z.string()
    .optional()
    .nullable()
    .transform(val => val === '' || val === 'none' ? null : val),
  capacity: z.number()
    .int()
    .min(1, 'Capacity must be at least 1'),
  utilization_target_percent: z.number()
    .min(0, 'Utilization target must be at least 0%')
    .max(100, 'Utilization target must be at most 100%'),
  calendar_id: z.string()
    .optional()
    .nullable()
    .transform(val => val === '' || val === 'none' ? null : val),
  overtime_allowed: z.boolean(),
  overtime_max_hours_per_day: z.number()
    .min(0, 'Overtime hours must be non-negative')
    .max(24, 'Overtime hours cannot exceed 24 per day'),
  overtime_cost_multiplier: z.number()
    .min(1, 'Overtime cost multiplier must be at least 1'),
  cost_per_time_unit: z.number()
    .min(0, 'Cost per time unit must be non-negative'),
  is_bottleneck: z.boolean(),
  is_active: z.boolean()
})

export type SequenceResourceFormData = z.infer<typeof sequenceResourceFormSchema>