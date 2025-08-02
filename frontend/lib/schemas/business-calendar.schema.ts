import { z } from 'zod'

export const businessCalendarFormSchema = z.object({
  name: z.string()
    .min(1, 'Calendar name is required')
    .max(255, 'Name must be 255 characters or less'),
  timezone: z.string()
    .min(1, 'Timezone is required'),
  default_start_time: z.number()
    .int()
    .min(0, 'Start time must be a valid time index')
    .max(95, 'Start time must be a valid time index'),
  default_end_time: z.number()
    .int()
    .min(0, 'End time must be a valid time index')
    .max(95, 'End time must be a valid time index'),
  working_days: z.array(z.boolean())
    .length(7, 'Working days must have exactly 7 values (one for each day of the week)'),
  is_default: z.boolean(),
  is_active: z.boolean()
}).refine(data => data.default_start_time < data.default_end_time, {
  message: 'Start time must be before end time',
  path: ['default_end_time']
})

export type BusinessCalendarFormData = z.infer<typeof businessCalendarFormSchema>