"use client"

import { UseFormReturn } from 'react-hook-form'
import { FormField, FormSection } from '@/components/forms/common/FormField'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'

interface MachineFormData {
  name: string
  code: string
  description: string
  machine_type: string
  department_id: string
  capacity_per_hour: number
  setup_time_minutes: number
  maintenance_interval_hours: number
  hourly_operating_cost: number
  is_active: boolean
  requires_skilled_operator: boolean
}

interface MachineFormFieldsProps {
  form: UseFormReturn<MachineFormData>
  departments: Array<{ department_id: string; name: string; code: string }>
  onFieldFocus?: (fieldName: string) => void | undefined
  onInteraction?: () => void | undefined
}

const machineTypes = [
  { value: 'cnc', label: 'CNC Machine' },
  { value: 'laser', label: 'Laser Cutter' },
  { value: 'welding', label: 'Welding Station' },
  { value: 'assembly', label: 'Assembly Line' },
  { value: 'packaging', label: 'Packaging Machine' },
  { value: 'testing', label: 'Testing Equipment' },
  { value: 'other', label: 'Other' }
]

export function MachineFormFields({ 
  form, 
  departments, 
  onFieldFocus, 
  onInteraction 
}: MachineFormFieldsProps) {
  const { register, formState: { errors }, watch, setValue } = form

  const handleFieldFocus = (fieldName: string) => {
    onFieldFocus?.(fieldName)
    onInteraction?.()
  }

  return (
    <div className="space-y-6">
      <FormSection title="Basic Information" description="General machine identification and classification">
        <div className="grid grid-cols-2 gap-4">
          <FormField 
            id="name" 
            label="Machine Name" 
            required 
            error={errors.name?.message}
          >
            <Input
              {...register('name', { required: 'Machine name is required' })}
              onFocus={() => handleFieldFocus('name')}
            />
          </FormField>

          <FormField 
            id="code" 
            label="Machine Code" 
            required 
            error={errors.code?.message}
            description="Unique identifier for this machine"
          >
            <Input
              {...register('code', { 
                required: 'Machine code is required',
                pattern: {
                  value: /^[A-Z0-9-]+$/,
                  message: 'Code must contain only uppercase letters, numbers, and hyphens'
                }
              })}
              onFocus={() => handleFieldFocus('code')}
              placeholder="e.g., CNC-001"
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
            onFocus={() => handleFieldFocus('description')}
            rows={3}
          />
        </FormField>

        <div className="grid grid-cols-2 gap-4">
          <FormField 
            id="machine_type" 
            label="Machine Type" 
            required 
            error={errors.machine_type?.message}
          >
            <Select
              value={watch('machine_type') || ''}
              onValueChange={(value) => {
                setValue('machine_type', value)
                onInteraction?.()
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select machine type" />
              </SelectTrigger>
              <SelectContent>
                {machineTypes.map(type => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField 
            id="department_id" 
            label="Department" 
            required 
            error={errors.department_id?.message}
          >
            <Select
              value={watch('department_id') || ''}
              onValueChange={(value) => {
                setValue('department_id', value)
                onInteraction?.()
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select department" />
              </SelectTrigger>
              <SelectContent>
                {departments.map(dept => (
                  <SelectItem key={dept.department_id} value={dept.department_id}>
                    {dept.name} ({dept.code})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>
        </div>
      </FormSection>

      <FormSection title="Operational Parameters" description="Configure machine capacity and timing">
        <div className="grid grid-cols-2 gap-4">
          <FormField 
            id="capacity_per_hour" 
            label="Capacity per Hour" 
            required 
            error={errors.capacity_per_hour?.message}
            description="Units produced per hour"
          >
            <Input
              type="number"
              {...register('capacity_per_hour', { 
                required: 'Capacity is required',
                min: { value: 1, message: 'Must be at least 1' }
              })}
              onFocus={() => handleFieldFocus('capacity_per_hour')}
            />
          </FormField>

          <FormField 
            id="setup_time_minutes" 
            label="Setup Time (minutes)" 
            required 
            error={errors.setup_time_minutes?.message}
            description="Time required for changeover"
          >
            <Input
              type="number"
              {...register('setup_time_minutes', { 
                required: 'Setup time is required',
                min: { value: 0, message: 'Must be 0 or greater' }
              })}
              onFocus={() => handleFieldFocus('setup_time_minutes')}
            />
          </FormField>

          <FormField 
            id="maintenance_interval_hours" 
            label="Maintenance Interval (hours)" 
            required 
            error={errors.maintenance_interval_hours?.message}
            description="Hours between maintenance"
          >
            <Input
              type="number"
              {...register('maintenance_interval_hours', { 
                required: 'Maintenance interval is required',
                min: { value: 1, message: 'Must be at least 1 hour' }
              })}
              onFocus={() => handleFieldFocus('maintenance_interval_hours')}
            />
          </FormField>

          <FormField 
            id="hourly_operating_cost" 
            label="Hourly Operating Cost ($)" 
            required 
            error={errors.hourly_operating_cost?.message}
          >
            <Input
              type="number"
              step="0.01"
              {...register('hourly_operating_cost', { 
                required: 'Operating cost is required',
                min: { value: 0, message: 'Must be 0 or greater' }
              })}
              onFocus={() => handleFieldFocus('hourly_operating_cost')}
            />
          </FormField>
        </div>
      </FormSection>

      <FormSection title="Configuration">
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="requires_skilled_operator"
              checked={watch('requires_skilled_operator')}
              onCheckedChange={(checked) => {
                setValue('requires_skilled_operator', checked as boolean)
                onInteraction?.()
              }}
            />
            <label 
              htmlFor="requires_skilled_operator"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Requires Skilled Operator
            </label>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="is_active"
              checked={watch('is_active')}
              onCheckedChange={(checked) => {
                setValue('is_active', checked as boolean)
                onInteraction?.()
              }}
            />
            <label 
              htmlFor="is_active"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Machine is Active
            </label>
          </div>
        </div>
      </FormSection>
    </div>
  )
}