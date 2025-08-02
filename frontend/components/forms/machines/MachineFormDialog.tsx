"use client"

import { UseFormReturn } from 'react-hook-form'
import { MachineFormData } from '@/lib/schemas'
import { Database } from '@/lib/database.types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { FormField, FormSection } from '@/components/forms/common/FormField'
import { Loader2 } from 'lucide-react'

type Department = Database['public']['Tables']['departments']['Row']
type WorkCell = Database['public']['Tables']['work_cells']['Row']

interface MachineFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  form: UseFormReturn<MachineFormData>
  departments: Department[]
  filteredWorkCells: WorkCell[]
  isSubmitting: boolean
  editingId: string | null
  onSubmit: (data: MachineFormData) => Promise<void>
  onCancel: () => void
  onDepartmentChange: (departmentId: string | null) => void
}

export function MachineFormDialog({
  open,
  onOpenChange,
  form,
  departments,
  filteredWorkCells,
  isSubmitting,
  editingId,
  onSubmit,
  onCancel,
  onDepartmentChange
}: MachineFormDialogProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch
  } = form

  const selectedDepartmentId = watch('department_id')

  const handleDepartmentChange = (value: string) => {
    setValue('department_id', value)
    setValue('cell_id', '') // Reset work cell when department changes
    onDepartmentChange(value || null)
  }

  const handleFormSubmit = (data: MachineFormData) => {
    onSubmit(data)
  }

  const handleCancel = () => {
    onCancel()
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {editingId ? 'Edit Machine' : 'Add New Machine'}
          </DialogTitle>
          <DialogDescription>
            {editingId 
              ? 'Update the machine details below.' 
              : 'Fill in the machine details below.'
            }
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
          <FormSection title="Basic Information">
            {/* Machine ID is auto-generated, not part of form */}

            <FormField
              id="name"
              label="Machine Name"
              error={errors.name?.message}
              required
            >
              <Input
                {...register('name')}
                placeholder="e.g., CNC Machine 1"
              />
            </FormField>

            {/* Description not in database schema */}
          </FormSection>

          <FormSection title="Location & Assignment">
            <FormField
              id="department_id"
              label="Department"
              error={errors.department_id?.message}
              required
            >
              <Select
                value={selectedDepartmentId}
                onValueChange={handleDepartmentChange}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select department" />
                </SelectTrigger>
                <SelectContent>
                  {departments.map((dept) => (
                    <SelectItem key={dept.department_id} value={dept.department_id}>
                      {dept.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </FormField>

            <FormField
              id="cell_id"
              label="Work Cell"
              error={errors.cell_id?.message}
            >
              <Select
                value={watch('cell_id') || ''}
                onValueChange={(value) => setValue('cell_id', value)}
                disabled={!selectedDepartmentId}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select work cell" />
                </SelectTrigger>
                <SelectContent>
                  {filteredWorkCells.map((cell) => (
                    <SelectItem key={cell.cell_id} value={cell.cell_id}>
                      {cell.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </FormField>
          </FormSection>

          <FormSection title="Capacity & Performance">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                id="capacity"
                label="Capacity"
                error={errors.capacity?.message}
                required
              >
                <Input
                  {...register('capacity', { valueAsNumber: true })}
                  type="number"
                  min="1"
                  placeholder="1"
                />
              </FormField>

              {/* Max concurrent jobs not in schema */}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                id="efficiency_rating"
                label="Efficiency Rating"
                error={errors.efficiency_rating?.message}
              >
                <Input
                  {...register('efficiency_rating', { valueAsNumber: true })}
                  type="number"
                  min="0"
                  max="100"
                  placeholder="100"
                />
              </FormField>

              <FormField
                id="average_utilization_percent"
                label="Average Utilization (%)"
                error={errors.average_utilization_percent?.message}
              >
                <Input
                  {...register('average_utilization_percent', { valueAsNumber: true })}
                  type="number"
                  min="0"
                  max="100"
                  placeholder="100"
                />
              </FormField>
            </div>
          </FormSection>

          <FormSection title="Operations & Costs">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                id="hourly_rate"
                label="Hourly Rate ($)"
                error={errors.hourly_rate?.message}
              >
                <Input
                  {...register('hourly_rate', { valueAsNumber: true })}
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                />
              </FormField>

              <FormField
                id="setup_time_minutes"
                label="Setup Time (minutes)"
                error={errors.setup_time_minutes?.message}
              >
                <Input
                  {...register('setup_time_minutes', { valueAsNumber: true })}
                  type="number"
                  min="0"
                  placeholder="0"
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                id="status"
                label="Status"
                error={errors.status?.message}
              >
                <Select
                  value={watch('status')}
                  onValueChange={(value) => setValue('status', value as any)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                    <SelectItem value="maintenance">Maintenance</SelectItem>
                  </SelectContent>
                </Select>
              </FormField>

              <FormField
                id="shift_pattern"
                label="Shift Pattern"
                error={errors.shift_pattern?.message}
              >
                <Select
                  value={watch('shift_pattern')}
                  onValueChange={(value) => setValue('shift_pattern', value as any)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select shift pattern" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="standard">Standard</SelectItem>
                    <SelectItem value="extended">Extended</SelectItem>
                    <SelectItem value="24/7">24/7</SelectItem>
                  </SelectContent>
                </Select>
              </FormField>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="maintenance_required"
                checked={watch('maintenance_required')}
                onCheckedChange={(checked) => 
                  setValue('maintenance_required', checked === true)
                }
              />
              <Label htmlFor="maintenance_required">
                Maintenance Required
              </Label>
            </div>
          </FormSection>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {editingId ? 'Update Machine' : 'Create Machine'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}