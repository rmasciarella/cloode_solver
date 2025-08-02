"use client"

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2 } from 'lucide-react'

const statusOptions = [
  { value: 'pending', label: 'Pending' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'on_hold', label: 'On Hold' }
]

interface JobInstanceFormFieldsProps {
  register: any
  setValue: any
  watch: any
  errors: any
  jobTemplates: any[]
  departments: any[]
  editingId: string | null
  isSubmitting: boolean
  onCancel: () => void
}

export function JobInstanceFormFields({
  register,
  setValue,
  watch,
  errors,
  jobTemplates,
  departments,
  editingId,
  isSubmitting,
  onCancel
}: JobInstanceFormFieldsProps) {
  return (
    <form className="space-y-4" role="form" aria-label="Job instance form">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Template - Required */}
        <div className="space-y-2">
          <Label htmlFor="template_id">Job Template *</Label>
          <Select 
            value={watch('template_id')} 
            onValueChange={(value) => setValue('template_id', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select job template" />
            </SelectTrigger>
            <SelectContent>
              {jobTemplates.map((template) => (
                <SelectItem key={template.template_id} value={template.template_id}>
                  {template.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {!watch('template_id') && <p className="text-sm text-red-600" role="alert">Job template is required</p>}
        </div>

        {/* Name - Required */}
        <div className="space-y-2">
          <Label htmlFor="name">Job Instance Name *</Label>
          <Input
            id="name"
            {...register('name', { 
              required: 'Job instance name is required',
              maxLength: { value: 255, message: 'Name must be 255 characters or less' }
            })}
            placeholder="e.g., Production Run #001"
            aria-describedby={errors.name ? "name-error" : undefined}
          />
          {errors.name && <p id="name-error" className="text-sm text-red-600" role="alert">{errors.name.message}</p>}
        </div>

        {/* Department */}
        <div className="space-y-2">
          <Label htmlFor="department_id">Department</Label>
          <Select 
            value={watch('department_id')} 
            onValueChange={(value) => setValue('department_id', value === 'none' ? '' : value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select department" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No Department</SelectItem>
              {departments.map((dept) => (
                <SelectItem key={dept.department_id} value={dept.department_id}>
                  {dept.name} ({dept.code})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Status */}
        <div className="space-y-2">
          <Label htmlFor="status">Status</Label>
          <Select 
            value={watch('status')} 
            onValueChange={(value) => setValue('status', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select status" />
            </SelectTrigger>
            <SelectContent>
              {statusOptions.map((status) => (
                <SelectItem key={status.value} value={status.value}>
                  {status.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Priority */}
        <div className="space-y-2">
          <Label htmlFor="priority">Priority</Label>
          <Input
            id="priority"
            type="number"
            min="1"
            {...register('priority', { 
              valueAsNumber: true,
              min: { value: 1, message: 'Priority must be at least 1' }
            })}
          />
          <p className="text-xs text-gray-500">Higher numbers = higher priority</p>
          {errors.priority && <p className="text-sm text-red-600" role="alert">{errors.priority.message}</p>}
        </div>

        {/* Quantity */}
        <div className="space-y-2">
          <Label htmlFor="quantity">Quantity</Label>
          <Input
            id="quantity"
            type="number"
            min="1"
            {...register('quantity', { 
              valueAsNumber: true,
              min: { value: 1, message: 'Quantity must be at least 1' }
            })}
          />
          {errors.quantity && <p className="text-sm text-red-600" role="alert">{errors.quantity.message}</p>}
        </div>

        {/* Due Date - CRITICAL for minimize lateness objective */}
        <div className="space-y-2">
          <Label htmlFor="due_date">Due Date</Label>
          <Input
            id="due_date"
            type="date"
            {...register('due_date')}
          />
          <p className="text-xs text-gray-500">Critical for minimize lateness objective</p>
        </div>

        {/* Earliest Start Date */}
        <div className="space-y-2">
          <Label htmlFor="earliest_start_date">Earliest Start Date</Label>
          <Input
            id="earliest_start_date"
            type="date"
            {...register('earliest_start_date', {
              required: 'Earliest start date is required'
            })}
            aria-describedby={errors.earliest_start_date ? "earliest-start-error" : undefined}
          />
          {errors.earliest_start_date && <p id="earliest-start-error" className="text-sm text-red-600" role="alert">{errors.earliest_start_date.message}</p>}
        </div>

        {/* Customer Order ID */}
        <div className="space-y-2">
          <Label htmlFor="customer_order_id">Customer Order ID</Label>
          <Input
            id="customer_order_id"
            {...register('customer_order_id')}
            placeholder="e.g., ORD-2024-001"
          />
        </div>

        {/* Batch ID */}
        <div className="space-y-2">
          <Label htmlFor="batch_id">Batch ID</Label>
          <Input
            id="batch_id"
            {...register('batch_id')}
            placeholder="e.g., BATCH-001"
          />
        </div>

        {/* Estimated Cost */}
        <div className="space-y-2">
          <Label htmlFor="estimated_cost">Estimated Cost ($)</Label>
          <Input
            id="estimated_cost"
            type="number"
            min="0"
            step="0.01"
            {...register('estimated_cost', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Cost must be non-negative' }
            })}
          />
          {errors.estimated_cost && <p className="text-sm text-red-600" role="alert">{errors.estimated_cost.message}</p>}
        </div>

        {/* Revenue Value */}
        <div className="space-y-2">
          <Label htmlFor="revenue_value">Revenue Value ($)</Label>
          <Input
            id="revenue_value"
            type="number"
            min="0"
            step="0.01"
            {...register('revenue_value', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Revenue must be non-negative' }
            })}
          />
          {errors.revenue_value && <p className="text-sm text-red-600" role="alert">{errors.revenue_value.message}</p>}
        </div>

        {/* Estimated Duration */}
        <div className="space-y-2">
          <Label htmlFor="estimated_duration_hours">Estimated Duration (hours)</Label>
          <Input
            id="estimated_duration_hours"
            type="number"
            min="0"
            step="0.1"
            {...register('estimated_duration_hours', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Duration must be non-negative' }
            })}
          />
          {errors.estimated_duration_hours && <p className="text-sm text-red-600" role="alert">{errors.estimated_duration_hours.message}</p>}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-2 pt-4">
        {editingId && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={isSubmitting || !watch('template_id')}>
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {editingId ? 'Update' : 'Create'} Job Instance
        </Button>
      </div>
    </form>
  )
}
