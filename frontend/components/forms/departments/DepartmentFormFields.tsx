"use client"

import { UseFormReturn } from 'react-hook-form'
import { DepartmentFormData } from '@/lib/schemas'
import { Database } from '@/lib/database.types'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { TimeInput } from '@/components/ui/time-input'
import { FormField, FormSection } from '@/components/forms/common/FormField'

type Department = Database['public']['Tables']['departments']['Row']

interface DepartmentFormFieldsProps {
  form: UseFormReturn<DepartmentFormData>
  departments: Department[]
  editingId?: string | null
  onFieldFocus?: (fieldName: string) => void
}

export function DepartmentFormFields({
  form,
  departments,
  editingId,
  onFieldFocus
}: DepartmentFormFieldsProps) {
  const { register, setValue, watch, formState: { errors } } = form

  // Allow all departments as potential parents, but prevent circular references
  const parentDepartments = departments.filter(dept => {
    // When creating new department, show all departments
    if (!editingId) return true
    
    // When editing, exclude self to prevent self-reference
    if (dept.department_id === editingId) return false
    
    // TODO: Add circular reference prevention logic here
    return true
  })

  return (
    <div className="space-y-6">
      <FormSection title="Basic Information" description="Core department details">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField
            id="code"
            label="Department Code"
            required
            error={errors.code?.message}
            description="Must be unique across all departments"
          >
            <Input
              {...register('code', { 
                required: 'Department code is required',
                maxLength: { value: 50, message: 'Code must be 50 characters or less' }
              })}
              placeholder="e.g., production, quality, DEPT_A"
              onFocus={() => onFieldFocus?.('code')}
            />
          </FormField>

          <FormField
            id="name"
            label="Department Name"
            required
            error={errors.name?.message}
          >
            <Input
              {...register('name', { 
                required: 'Department name is required',
                maxLength: { value: 255, message: 'Name must be 255 characters or less' }
              })}
              placeholder="e.g., Production Department"
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
            placeholder="Department description and responsibilities"
            rows={3}
            onFocus={() => onFieldFocus?.('description')}
          />
        </FormField>
      </FormSection>

      <FormSection title="Department Structure" description="Hierarchy and organization">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField
            id="parent_department_id"
            label="Parent Department"
            description={
              <span>
                <strong>For single department use:</strong> Select "None (Root Department)" to make this a top-level department.<br/>
                <strong>For hierarchy:</strong> Child departments inherit scheduling constraints from parent.
              </span>
            }
          >
            <Select 
              value={watch('parent_department_id') || undefined}
              onValueChange={(value) => {
                setValue('parent_department_id', value)
                onFieldFocus?.('parent_department_id')
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select parent department" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None (Root Department)</SelectItem>
                {parentDepartments.map((dept) => (
                  <SelectItem key={dept.department_id} value={dept.department_id}>
                    {dept.name} ({dept.code})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField
            id="cost_center"
            label="Cost Center Code"
            error={errors.cost_center?.message}
            description="Optional: For financial tracking and cost allocation (not currently mapped to solver constraints)"
          >
            <Input
              {...register('cost_center')}
              placeholder="e.g., CC-PROD-001"
              onFocus={() => onFieldFocus?.('cost_center')}
            />
          </FormField>
        </div>
      </FormSection>

      <FormSection title="Default Shift Times" description="Standard working hours for this department">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TimeInput
            label="Default Shift Start Time"
            value={watch('default_shift_start') || 32}
            onChange={(index) => {
              setValue('default_shift_start', index)
              onFieldFocus?.('default_shift_start')
            }}
            id="default_shift_start"
            placeholder="Select start time"
            helperText="Default start time for this department's shifts"
            required
          />

          <TimeInput
            label="Default Shift End Time"
            value={watch('default_shift_end') || 64}
            onChange={(index) => {
              setValue('default_shift_end', index)
              onFieldFocus?.('default_shift_end')
            }}
            id="default_shift_end"
            placeholder="Select end time"
            helperText="Default end time for this department's shifts"
            required
          />
        </div>
      </FormSection>

      <FormSection title="Settings" description="Department configuration options">
        <div className="flex flex-col space-y-4">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="overtime_allowed"
              checked={watch('overtime_allowed')}
              onCheckedChange={(checked) => {
                setValue('overtime_allowed', checked as boolean)
                onFieldFocus?.('overtime_allowed')
              }}
            />
            <Label htmlFor="overtime_allowed">Overtime Allowed</Label>
          </div>

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
        </div>
      </FormSection>
    </div>
  )
}