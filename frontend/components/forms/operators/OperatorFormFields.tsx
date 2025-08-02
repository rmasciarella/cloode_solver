"use client"

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2 } from 'lucide-react'

const employmentStatuses = [
  { value: 'active', label: 'Active' },
  { value: 'on_leave', label: 'On Leave' },
  { value: 'terminated', label: 'Terminated' },
  { value: 'retired', label: 'Retired' }
]

interface OperatorFormFieldsProps {
  register: any
  setValue: any
  watch: any
  errors: any
  departments: any[]
  editingId: string | null
  isSubmitting: boolean
  onCancel: () => void
}

export function OperatorFormFields({
  register,
  setValue,
  watch,
  errors,
  departments,
  editingId,
  isSubmitting,
  onCancel
}: OperatorFormFieldsProps) {
  return (
    <form className="space-y-4" role="form" aria-label="Operator form">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Name - Required */}
        <div className="space-y-2">
          <Label htmlFor="name">Operator Name *</Label>
          <Input
            id="name"
            {...register('name', { 
              required: 'Operator name is required',
              maxLength: { value: 255, message: 'Name must be 255 characters or less' }
            })}
            placeholder="e.g., John Smith"
            aria-describedby={errors.name ? "name-error" : undefined}
          />
          {errors.name && <p id="name-error" className="text-sm text-red-600" role="alert">{errors.name.message}</p>}
        </div>

        {/* Employee Number */}
        div className="space-y-2"
          Label htmlFor="employee_number"Employee Number/Label
          Input
            id="employee_number"
            {...register('employee_number')}
            placeholder="e.g., EMP-001"
          /
        /div

        {/* Department */}
        div className="space-y-2"
          Label htmlFor="department_id"Department/Label
          Select onValueChange={(value) = setValue('department_id', value)}
            SelectTrigger
              SelectValue placeholder="Select department" /
            /SelectTrigger
            SelectContent
              SelectItem value="none"No Department/SelectItem
              {departments.map((dept) = (
                SelectItem key={dept.department_id} value={dept.department_id}
                  {dept.name} ({dept.code})
                /SelectItem
              ))}
            /SelectContent
          /Select
        /div

        {/* Employment Status */}
        div className="space-y-2"
          Label htmlFor="employment_status"Employment Status/Label
          Select onValueChange={(value) = setValue('employment_status', value)}
            SelectTrigger
              SelectValue placeholder="Select status" /
            /SelectTrigger
            SelectContent
              {employmentStatuses.map((status) = (
                SelectItem key={status.value} value={status.value}
                  {status.label}
                /SelectItem
              ))}
            /SelectContent
          /Select
        /div

        {/* Hourly Rate */}
        div className="space-y-2"
          Label htmlFor="hourly_rate"Hourly Rate ($)/Label
          Input
            id="hourly_rate"
            type="number"
            min="0"
            step="0.01"
            {...register('hourly_rate', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Rate must be non-negative' }
            })}
            aria-describedby={errors.hourly_rate ? "hourly-rate-error" : undefined}
          /
          {errors.hourly_rate  p id="hourly-rate-error" className="text-sm text-red-600" role="alert"{errors.hourly_rate.message}/p}
        /div

        {/* Max Hours Per Day */}
        div className="space-y-2"
          Label htmlFor="max_hours_per_day"Max Hours Per Day/Label
          Input
            id="max_hours_per_day"
            type="number"
            min="1"
            max="24"
            {...register('max_hours_per_day', { 
              valueAsNumber: true,
              min: { value: 1, message: 'Must be at least 1 hour' },
              max: { value: 24, message: 'Cannot exceed 24 hours' }
            })}
          /
          {errors.max_hours_per_day  p className="text-sm text-red-600" role="alert"{errors.max_hours_per_day.message}/p}
        /div

        {/* Max Hours Per Week */}
        div className="space-y-2"
          Label htmlFor="max_hours_per_week"Max Hours Per Week/Label
          Input
            id="max_hours_per_week"
            type="number"
            min="1"
            max="168"
            {...register('max_hours_per_week', { 
              valueAsNumber: true,
              min: { value: 1, message: 'Must be at least 1 hour' },
              max: { value: 168, message: 'Cannot exceed 168 hours per week' }
            })}
          /
          {errors.max_hours_per_week  p className="text-sm text-red-600" role="alert"{errors.max_hours_per_week.message}/p}
        /div

        {/* Overtime Rate Multiplier */}
        div className="space-y-2"
          Label htmlFor="overtime_rate_multiplier"Overtime Rate Multiplier/Label
          Input
            id="overtime_rate_multiplier"
            type="number"
            min="1"
            step="0.1"
            {...register('overtime_rate_multiplier', { 
              valueAsNumber: true,
              min: { value: 1, message: 'Multiplier must be at least 1.0' }
            })}
          /
          {errors.overtime_rate_multiplier  p className="text-sm text-red-600" role="alert"{errors.overtime_rate_multiplier.message}/p}
        /div

        {/* Efficiency Rating */}
        div className="space-y-2"
          Label htmlFor="efficiency_rating"Efficiency Rating/Label
          Input
            id="efficiency_rating"
            type="number"
            min="0"
            step="0.01"
            {...register('efficiency_rating', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Rating must be non-negative' }
            })}
            aria-describedby={errors.efficiency_rating ? "efficiency-rating-error" : undefined}
          /
          {errors.efficiency_rating  p id="efficiency-rating-error" className="text-sm text-red-600" role="alert"{errors.efficiency_rating.message}/p}
        /div

        {/* Quality Score */}
        div className="space-y-2"
          Label htmlFor="quality_score"Quality Score/Label
          Input
            id="quality_score"
            type="number"
            min="0"
            step="0.01"
            {...register('quality_score', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Score must be non-negative' }
            })}
            aria-describedby={errors.quality_score ? "quality-score-error" : undefined}
          /
          {errors.quality_score  p id="quality-score-error" className="text-sm text-red-600" role="alert"{errors.quality_score.message}/p}
        /div

        {/* Safety Score */}
        div className="space-y-2"
          Label htmlFor="safety_score"Safety Score/Label
          Input
            id="safety_score"
            type="number"
            min="0"
            step="0.01"
            {...register('safety_score', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Score must be non-negative' }
            })}
            aria-describedby={errors.safety_score ? "safety-score-error" : undefined}
          /
          {errors.safety_score  p id="safety-score-error" className="text-sm text-red-600" role="alert"{errors.safety_score.message}/p}
        /div

        {/* Hire Date */}
        div className="space-y-2"
          Label htmlFor="hire_date"Hire Date/Label
          Input
            id="hire_date"
            type="date"
            {...register('hire_date')}
          /
        /div
      /div

      {/* Active Checkbox */}
      div className="flex items-center space-x-2"
        Checkbox
          id="is_active"
          checked={watch('is_active')}
          onCheckedChange={(checked) = setValue('is_active', !!checked)}
        /
        Label htmlFor="is_active"Active/Label
      /div

      {/* Action Buttons */}
      div className="flex justify-end space-x-2 pt-4"
        {editingId  (
          Button type="button" variant="outline" onClick={onCancel}
            Cancel
          /Button
        )}
        Button type="submit" disabled={isSubmitting}
          {isSubmitting  Loader2 className="mr-2 h-4 w-4 animate-spin" /}
          {editingId ? 'Update' : 'Create'} Operator
        /Button
      /div
    /form
  )
}
