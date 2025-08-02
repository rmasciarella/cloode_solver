"use client"

import { cellTypes } from '@/lib/schemas'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2 } from 'lucide-react'

interface WorkCellFormFieldsProps {
  register: any
  setValue: any
  watch: any
  errors: any
  departments: any[]
  editingId: string | null
  isSubmitting: boolean
  onCancel: () => void
}

export function WorkCellFormFields({
  register,
  setValue,
  watch,
  errors,
  departments,
  editingId,
  isSubmitting,
  onCancel
}: WorkCellFormFieldsProps) {
  return (
    <form className="space-y-4" role="form" aria-label="Work cell form">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Name - Required */}
        <div className="space-y-2">
          <Label htmlFor="name">Cell Name *</Label>
          <Input
            id="name"
            {...register('name')}
            placeholder="e.g., Production Cell A"
            aria-describedby={errors.name ? "name-error" : undefined}
          />
          {errors.name && <p id="name-error" className="text-sm text-red-600" role="alert">{errors.name.message}</p>}
        </div>

        {/* Cell Type */}
        <div className="space-y-2">
          <Label htmlFor="cell_type">Cell Type</Label>
          <Select onValueChange={(value) => setValue('cell_type', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select cell type" />
            </SelectTrigger>
            <SelectContent>
              {cellTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Department */}
        <div className="space-y-2">
          <Label htmlFor="department_id">Department</Label>
          <Select onValueChange={(value) => setValue('department_id', value)}>
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

        {/* Floor Location */}
        <div className="space-y-2">
          <Label htmlFor="floor_location">Floor Location</Label>
          <Input
            id="floor_location"
            {...register('floor_location')}
            placeholder="e.g., Building A, Floor 2, Zone 3"
          />
        </div>

        {/* Capacity */}
        <div className="space-y-2">
          <Label htmlFor="capacity">Capacity</Label>
          <Input
            id="capacity"
            type="number"
            min="1"
            {...register('capacity', { valueAsNumber: true })}
            aria-describedby={errors.capacity ? "capacity-error" : undefined}
          />
          {errors.capacity && <p id="capacity-error" className="text-sm text-red-600" role="alert">{errors.capacity.message}</p>}
        </div>

        {/* WIP Limit */}
        <div className="space-y-2">
          <Label htmlFor="wip_limit">WIP Limit</Label>
          <Input
            id="wip_limit"
            type="number"
            min="0"
            {...register('wip_limit', { valueAsNumber: true })}
          />
          <p className="text-xs text-gray-500">Work-in-progress limit for constraint generation</p>
          {errors.wip_limit && <p className="text-sm text-red-600" role="alert">{errors.wip_limit.message}</p>}
        </div>

        {/* Target Utilization % */}
        <div className="space-y-2">
          <Label htmlFor="utilization_target_percent">Target Utilization (%)</Label>
          <Input
            id="utilization_target_percent"
            type="number"
            min="0"
            max="100"
            step="0.1"
            {...register('target_utilization', { valueAsNumber: true })}
            placeholder="85.0"
          />
          <p className="text-xs text-gray-500">Target capacity utilization percentage for optimization</p>
          {errors.target_utilization && <p className="text-sm text-red-600" role="alert">{errors.target_utilization.message}</p>}
        </div>

        {/* Flow Priority */}
        <div className="space-y-2">
          <Label htmlFor="flow_priority">Flow Priority</Label>
          <Input
            id="flow_priority"
            type="number"
            min="1"
            {...register('flow_priority', { 
              valueAsNumber: true,
              min: { value: 1, message: 'Priority must be at least 1' }
            })}
          />
          <p className="text-xs text-gray-500">Higher numbers = higher priority</p>
          {errors.flow_priority && <p className="text-sm text-red-600" role="alert">{errors.flow_priority.message}</p>}
        </div>
      </div>

      {/* Active Checkbox */}
      <div className="flex items-center space-x-2">
        <Checkbox
          id="is_active"
          checked={watch('is_active')}
          onCheckedChange={(checked) => setValue('is_active', !!checked)}
        />
        <Label htmlFor="is_active">Active</Label>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-2 pt-4">
        {editingId && (
          <Button 
            type="button" 
            variant="outline" 
            onClick={onCancel}
          >
            Cancel
          </Button>
        )}
        <Button 
          type="submit" 
          disabled={isSubmitting}
        >
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {editingId ? 'Update' : 'Create'} Work Cell
        </Button>
      </div>
    </form>
  )
}
