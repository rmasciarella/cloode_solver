import { z } from 'zod'

export const skillFormSchema = z.object({
  code: z.string()
    .min(1, 'Skill code is required')
    .max(50, 'Code must be 50 characters or less')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Code can only contain letters, numbers, underscores, and hyphens'),
  name: z.string()
    .min(1, 'Skill name is required')
    .max(255, 'Name must be 255 characters or less'),
  description: z.string()
    .optional()
    .transform(val => val === '' ? undefined : val),
  category: z.string()
    .min(1, 'Category is required'),
  proficiency_levels: z.array(z.string())
    .min(1, 'At least one proficiency level is required'),
  complexity_rating: z.number()
    .int()
    .min(1, 'Complexity rating must be at least 1')
    .max(10, 'Complexity rating must be at most 10'),
  requires_certification: z.boolean(),
  certification_name: z.string()
    .optional()
    .transform(val => val === '' ? undefined : val),
  certification_expiry_days: z.number()
    .optional()
    .nullable()
    .transform(val => val === undefined || val === null || val === 0 ? null : val),
  base_learning_hours: z.number()
    .min(0, 'Learning hours must be non-negative'),
  retention_factor: z.number()
    .min(0, 'Retention factor must be non-negative')
    .max(1, 'Retention factor must be at most 1'),
  is_active: z.boolean()
}).refine(data => {
  // If certification is required, certification name must be provided
  if (data.requires_certification && !data.certification_name) {
    return false
  }
  return true
}, {
  message: 'Certification name is required when certification is required',
  path: ['certification_name']
})

export type SkillFormData = z.infer<typeof skillFormSchema>