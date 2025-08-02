import { z } from 'zod'

export const maintenanceTypeSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  is_preventive: z.boolean(),
  is_emergency: z.boolean(),
  typical_duration_hours: z.number().min(0.1, 'Duration must be positive'),
  blocks_production: z.boolean(),
  allows_emergency_override: z.boolean(),
  requires_shutdown: z.boolean(),
  required_skill_level: z.string().optional(),
  requires_external_vendor: z.boolean()
})

export type MaintenanceTypeFormData = z.infer<typeof maintenanceTypeSchema>

export const skillLevels = [
  { value: 'NOVICE', label: 'Novice' },
  { value: 'COMPETENT', label: 'Competent' },
  { value: 'PROFICIENT', label: 'Proficient' },
  { value: 'EXPERT', label: 'Expert' }
] as const