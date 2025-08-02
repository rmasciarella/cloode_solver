"use client"

import { UseFormReturn } from 'react-hook-form'
import { FormField, FormSection } from '@/components/forms/common/FormField'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'

// Form data that matches the database schema
interface MachineFormData {
  name: string
  capacity: number  // Changed from capacity_per_hour
  cost_per_hour: number  // Changed from hourly_operating_cost
  department_id: string
  cell_id: string
  setup_time_minutes: number
  teardown_time_minutes: number
  maintenance_interval_hours: number
  machine_type: string
  is_active: boolean
  // Additional fields for user convenience (not in database)
  code?: string | undefined
  description?: string | undefined
  requires_skilled_operator?: boolean | undefined
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

export function MachineFormFieldsRefactored({ 
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
      <FormSection title="Basic Information" description="Machine identification and description">
        <FormField 
          id="name" 
          label="Machine Name" 
          required 
          error={errors.name?.message}
          description="Display name for the machine"
        >
          <Input
            {...register('name', { required: 'Machine name is required' })}
            onFocus={() => handleFieldFocus('name')}
            placeholder="e.g., CNC Mill 1"
          />
        </FormField>

        <FormField 
          id="code" 
          label="Machine Code" 
          error={errors.code?.message}
          description="Optional unique identifier (auto-generated if not provided)"
        >
          <Input
            {...register('code')}
            onFocus={() => handleFieldFocus('code')}
            placeholder="e.g., CNC-001"
          />
        </FormField>

        <FormField 
          id="description" 
          label="Description" 
          error={errors.description?.message}
          description="Optional detailed description"
        >
          <Textarea
            {...register('description')}
            onFocus={() => handleFieldFocus('description')}
            rows={3}
            placeholder="e.g., High precision 5-axis CNC milling machine"
          />
        </FormField>
      </FormSection>

      <FormSection title="Configuration" description="Machine type and operational settings">
        <div className="grid grid-cols-2 gap-4">
          <FormField 
            id="machine_type" 
            label="Machine Type" 
            required 
            error={errors.machine_type?.message}
            description="Category of machine"
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
            error={errors.department_id?.message}
            description="Assigned department"
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
                <SelectItem value="">None</SelectItem>
                {departments.map(dept => (
                  <SelectItem key={dept.department_id} value={dept.department_id}>
                    {dept.name} ({dept.code})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>
        </div>

        <FormField 
          id="cell_id" 
          label="Work Cell ID" 
          required 
          error={errors.cell_id?.message}
          description="The work cell this machine belongs to"
        >
          <Input
            {...register('cell_id', { required: 'Work cell ID is required' })}
            onFocus={() => handleFieldFocus('cell_id')}
            placeholder="e.g., cell_123"
          />
        </FormField>
      </FormSection>

      <FormSection title="Capacity & Cost" description="Production capacity and operating costs">
        <div className="grid grid-cols-2 gap-4">
          <FormField 
            id="capacity" 
            label="Capacity (units/hour)" 
            required 
            error={errors.capacity?.message}
            description="Production capacity per hour"
          >
            <Input
              type="number"
              {...register('capacity', { 
                required: 'Capacity is required',
                min: { value: 1, message: 'Must be at least 1' }
              })}
              onFocus={() => handleFieldFocus('capacity')}
              placeholder="10"
            />
          </FormField>

          <FormField 
            id="cost_per_hour" 
            label="Operating Cost ($/hour)" 
            required 
            error={errors.cost_per_hour?.message}
            description="Cost per hour of operation"
          >
            <Input
              type="number"
              step="0.01"
              {...register('cost_per_hour', { 
                required: 'Operating cost is required',
                min: { value: 0, message: 'Must be 0 or greater' }
              })}
              onFocus={() => handleFieldFocus('cost_per_hour')}
              placeholder="85.50"
            />
          </FormField>
        </div>
      </FormSection>

      <FormSection title="Setup & Maintenance" description="Setup times and maintenance schedule">
        <div className="grid grid-cols-2 gap-4">
          <FormField 
            id="setup_time_minutes" 
            label="Setup Time (minutes)" 
            required 
            error={errors.setup_time_minutes?.message}
            description="Default setup/changeover time"
          >
            <Input
              type="number"
              {...register('setup_time_minutes', { 
                required: 'Setup time is required',
                min: { value: 0, message: 'Must be 0 or greater' }
              })}
              onFocus={() => handleFieldFocus('setup_time_minutes')}
              placeholder="30"
            />
          </FormField>

          <FormField 
            id="teardown_time_minutes" 
            label="Teardown Time (minutes)" 
            required 
            error={errors.teardown_time_minutes?.message}
            description="Time needed for teardown"
          >
            <Input
              type="number"
              {...register('teardown_time_minutes', { 
                required: 'Teardown time is required',
                min: { value: 0, message: 'Must be 0 or greater' }
              })}
              onFocus={() => handleFieldFocus('teardown_time_minutes')}
              placeholder="15"
            />
          </FormField>
        </div>

        <FormField 
          id="maintenance_interval_hours" 
          label="Maintenance Interval (hours)" 
          required 
          error={errors.maintenance_interval_hours?.message}
          description="Hours between scheduled maintenance"
        >
          <Input
            type="number"
            {...register('maintenance_interval_hours', { 
              required: 'Maintenance interval is required',
              min: { value: 1, message: 'Must be at least 1' }
            })}
            onFocus={() => handleFieldFocus('maintenance_interval_hours')}
            placeholder="200"
          />
        </FormField>
      </FormSection>

      <FormSection title="Status & Requirements" description="Machine status and operator requirements">
        <div className="space-y-3">
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
              <span className="text-xs text-gray-500 ml-1">
                (Available for production scheduling)
              </span>
            </label>
          </div>

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
              <span className="text-xs text-gray-500 ml-1">
                (Special certification or training required)
              </span>
            </label>
          </div>
        </div>
      </FormSection>
    </div>
  )
}