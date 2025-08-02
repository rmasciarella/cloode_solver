"use client"

import { UseFormReturn } from 'react-hook-form'
import { SequenceResourceFormData } from '@/hooks/forms/useSequenceResourceForm'
import { Database } from '@/lib/database.types'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { FormField, FormSection } from '@/components/forms/common/FormField'

type Department = Database['public']['Tables']['departments']['Row']

interface SequenceResourceFormFieldsProps {
  form: UseFormReturn<SequenceResourceFormData>
  departments: Department[]
  editingId?: string | null
  onFieldFocus?: (fieldName: string) => void
}

const resourceTypes = [
  { value: 'exclusive', label: 'Exclusive' },
  { value: 'shared', label: 'Shared' },
  { value: 'pooled', label: 'Pooled' }
]

export function SequenceResourceFormFields({
  form,
  departments,
  editingId,
  onFieldFocus
}: SequenceResourceFormFieldsProps) {
  const { register, setValue, watch, formState: { errors } } = form

  return (
    <div className="space-y-6">
      <FormSection title="Basic Information" description="Core sequence resource details">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField
            id="sequence_id"
            label="Sequence ID"
            required
            error={errors.sequence_id?.message}
            description="Unique identifier for this sequence resource"
          >
            <Input
              {...register('sequence_id', { 
                required: 'Sequence ID is required',
                maxLength: { value: 50, message: 'ID must be 50 characters or less' }
              })}
              placeholder="e.g., OPTO_001, WELD_SEQ_A"
              onFocus={() => onFieldFocus?.('sequence_id')}
              disabled={!!editingId} // Don't allow editing ID
            />
          </FormField>

          <FormField
            id="name"
            label="Name"
            required
            error={errors.name?.message}
          >
            <Input
              {...register('name', { 
                required: 'Name is required',
                maxLength: { value: 255, message: 'Name must be 255 characters or less' }
              })}
              placeholder="e.g., Optical Testing Sequence"
              onFocus={() => onFieldFocus?.('name')}
            />
          </FormField>
        </div>

        <FormField
          id="description"
          label="Description"
          error={errors.description?.message}
        >
          <Textarea
            {...register('description')}
            placeholder="Description of the sequence resource workflow and purpose"
            rows={3}
            onFocus={() => onFieldFocus?.('description')}
          />
        </FormField>
      </FormSection>

      <FormSection title="Resource Configuration" description="Technical specifications and constraints">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField
            id="resource_type"
            label="Resource Type"
            required
            description="Exclusive: One job at a time, Shared: Multiple jobs possible, Pooled: Resource from a pool"
          >
            <Select 
              value={watch('resource_type') || undefined}
              onValueChange={(value) => {
                setValue('resource_type', value as 'exclusive' | 'shared' | 'pooled')
                onFieldFocus?.('resource_type')
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select resource type" />
              </SelectTrigger>
              <SelectContent>
                {resourceTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField
            id="max_concurrent_jobs"
            label="Max Concurrent Jobs"
            required
            error={errors.max_concurrent_jobs?.message}
            description="Maximum number of jobs that can use this resource simultaneously"
          >
            <Input
              id="max_concurrent_jobs"
              type="number"
              min="1"
              {...register('max_concurrent_jobs', { 
                valueAsNumber: true,
                min: { value: 1, message: 'Must allow at least 1 concurrent job' }
              })}
              onFocus={() => onFieldFocus?.('max_concurrent_jobs')}
            />
          </FormField>

          <FormField
            id="priority"
            label="Priority"
            required
            error={errors.priority?.message}
            description="Higher numbers = higher priority (1 = lowest)"
          >
            <Input
              id="priority"
              type="number"
              min="1"
              {...register('priority', { 
                valueAsNumber: true,
                min: { value: 1, message: 'Priority must be at least 1' }
              })}
              onFocus={() => onFieldFocus?.('priority')}
            />
          </FormField>

          <FormField
            id="department_id"
            label="Department"
            description="Optional: Associate this resource with a specific department"
          >
            <Select 
              value={watch('department_id') || undefined}
              onValueChange={(value) => {
                setValue('department_id', value)
                onFieldFocus?.('department_id')
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select department (optional)" />
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
          </FormField>
        </div>
      </FormSection>

      <FormSection title="Timing Configuration" description="Setup and teardown time requirements">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField
            id="setup_time_minutes"
            label="Setup Time (minutes)"
            required
            error={errors.setup_time_minutes?.message}
            description="Time required to prepare this resource for a job"
          >
            <Input
              id="setup_time_minutes"
              type="number"
              min="0"
              {...register('setup_time_minutes', { 
                valueAsNumber: true,
                min: { value: 0, message: 'Setup time must be non-negative' }
              })}
              onFocus={() => onFieldFocus?.('setup_time_minutes')}
            />
          </FormField>

          <FormField
            id="teardown_time_minutes"
            label="Teardown Time (minutes)"
            required
            error={errors.teardown_time_minutes?.message}
            description="Time required to clean up after job completion"
          >
            <Input
              id="teardown_time_minutes"
              type="number"
              min="0"
              {...register('teardown_time_minutes', { 
                valueAsNumber: true,
                min: { value: 0, message: 'Teardown time must be non-negative' }
              })}
              onFocus={() => onFieldFocus?.('teardown_time_minutes')}
            />
          </FormField>
        </div>
      </FormSection>

      <FormSection title="Settings" description="Resource availability and status">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="is_active"
            checked={watch('is_active')}
            onCheckedChange={(checked) => {
              setValue('is_active', checked as boolean)
              onFieldFocus?.('is_active')
            }}
          />
          <Label htmlFor="is_active">Active</Label>
        </div>
      </FormSection>
    </div>
  )
}
