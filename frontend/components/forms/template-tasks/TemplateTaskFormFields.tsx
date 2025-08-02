"use client"

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2 } from 'lucide-react'

type JobOptimizedPattern = {
  pattern_id: string
  name: string
}

type Department = {
  department_id: string
  name: string
  code: string
}

type SequenceResource = {
  sequence_id: string
  name: string
}

interface TemplateTaskFormFieldsProps {
  register: any
  setValue: (name: string, value: any) => void
  watch: (name?: string) => any
  errors: any
  editingId: string | null
  isSubmitting: boolean
  handleCancel: () => void
  jobOptimizedPatterns: JobOptimizedPattern[]
  departments: Department[]
  sequenceResources: SequenceResource[]
}

const efficiencyCurves = [
  { value: 'linear', label: 'Linear' },
  { value: 'exponential', label: 'Exponential' },
  { value: 'logarithmic', label: 'Logarithmic' },
  { value: 'plateau', label: 'Plateau' }
]

export function TemplateTaskFormFields({
  register,
  setValue,
  watch,
  errors,
  editingId,
  isSubmitting,
  handleCancel,
  jobOptimizedPatterns,
  departments,
  sequenceResources
}: TemplateTaskFormFieldsProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Template - Required */}
        <div className="space-y-2">
          <Label htmlFor="pattern_id">Job Optimized Pattern *</Label>
          <Select onValueChange={(value) => setValue('pattern_id', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select job optimized pattern" />
            </SelectTrigger>
            <SelectContent>
              {jobOptimizedPatterns.map((pattern) => (
                <SelectItem key={pattern.pattern_id} value={pattern.pattern_id}>
                  {pattern.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {!watch('pattern_id') && <p className="text-sm text-red-600">Job optimized pattern is required</p>}
        </div>

        {/* Name - Required */}
        <div className="space-y-2">
          <Label htmlFor="name">Task Name *</Label>
          <Input
            id="name"
            {...register('name', { 
              required: 'Task name is required',
              maxLength: { value: 255, message: 'Name must be 255 characters or less' }
            })}
            placeholder="e.g., Assembly Step 1"
          />
          {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
        </div>

        {/* Position - Required */}
        <div className="space-y-2">
          <Label htmlFor="position">Position *</Label>
          <Input
            id="position"
            type="number"
            min="1"
            {...register('position', { 
              valueAsNumber: true,
              required: 'Position is required',
              min: { value: 1, message: 'Position must be at least 1' }
            })}
          />
          {errors.position && <p className="text-sm text-red-600">{errors.position.message}</p>}
        </div>

        {/* Department - Required */}
        <div className="space-y-2">
          <Label htmlFor="department_id">Department *</Label>
          <Select onValueChange={(value) => setValue('department_id', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select department" />
            </SelectTrigger>
            <SelectContent>
              {departments.map((dept) => (
                <SelectItem key={dept.department_id} value={dept.department_id}>
                  {dept.name} ({dept.code})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {!watch('department_id') && <p className="text-sm text-red-600">Department is required</p>}
        </div>

        {/* Sequence Resource */}
        <div className="space-y-2">
          <Label htmlFor="sequence_id">Sequence Resource</Label>
          <Select onValueChange={(value) => setValue('sequence_id', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select sequence resource" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No Sequence Resource</SelectItem>
              {sequenceResources.map((resource) => (
                <SelectItem key={resource.sequence_id} value={resource.sequence_id}>
                  {resource.name} ({resource.sequence_id})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Minimum Operators */}
        <div className="space-y-2">
          <Label htmlFor="min_operators">Minimum Operators</Label>
          <Input
            id="min_operators"
            type="number"
            min="1"
            {...register('min_operators', { 
              valueAsNumber: true,
              min: { value: 1, message: 'Must have at least 1 operator' }
            })}
          />
          {errors.min_operators && <p className="text-sm text-red-600">{errors.min_operators.message}</p>}
        </div>

        {/* Maximum Operators */}
        <div className="space-y-2">
          <Label htmlFor="max_operators">Maximum Operators</Label>
          <Input
            id="max_operators"
            type="number"
            min="1"
            {...register('max_operators', { 
              valueAsNumber: true,
              min: { value: 1, message: 'Must have at least 1 operator' },
              validate: (value) => {
                const minOps = watch('min_operators') || 1
                return value >= minOps || 'Maximum must be >= minimum operators'
              }
            })}
          />
          {errors.max_operators && <p className="text-sm text-red-600">{errors.max_operators.message}</p>}
        </div>
      </div>

      {/* Checkboxes */}
      <div className="flex flex-col space-y-4">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="is_unattended"
            checked={watch('is_unattended')}
            onCheckedChange={(checked) => setValue('is_unattended', checked as boolean)}
          />
          <Label htmlFor="is_unattended">Unattended Operation</Label>
          <p className="text-xs text-gray-500 ml-2">Task can run without operator supervision</p>
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox
            id="is_setup"
            checked={watch('is_setup')}
            onCheckedChange={(checked) => setValue('is_setup', checked as boolean)}
          />
          <Label htmlFor="is_setup">Setup Task</Label>
          <p className="text-xs text-gray-500 ml-2">This is a setup or preparation task</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="operator_efficiency_curve">Operator Efficiency Curve</Label>
          <Select value={watch('operator_efficiency_curve')} onValueChange={(value) => setValue('operator_efficiency_curve', value)}>
            <SelectTrigger id="operator_efficiency_curve">
              <SelectValue placeholder="Select efficiency curve" />
            </SelectTrigger>
            <SelectContent>
              {efficiencyCurves.map((curve) => (
                <SelectItem key={curve.value} value={curve.value}>
                  {curve.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-gray-500">How operator efficiency changes with experience</p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-2 pt-4">
        {editingId && (
          <Button type="button" variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={isSubmitting || !watch('pattern_id') || !watch('department_id')}>
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {editingId ? 'Update' : 'Create'} Task
        </Button>
      </div>
    </div>
  )
}
