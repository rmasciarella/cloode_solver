"use client"

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2 } from 'lucide-react'

type OptimizedTask = {
  optimized_task_id: string
  name: string
  pattern_id: string
  pattern_name: string
}

type JobOptimizedPattern = {
  pattern_id: string
  name: string
}

interface TemplatePrecedenceFormFieldsProps {
  register: any
  setValue: (name: string, value: any) => void
  watch: (name?: string) => any
  errors: any
  editingId: string | null
  isSubmitting: boolean
  handleCancel: () => void
  optimizedTasks: OptimizedTask[]
  patterns: JobOptimizedPattern[]
}

export function TemplatePrecedenceFormFields({
  register,
  setValue,
  watch,
  errors,
  editingId,
  isSubmitting,
  handleCancel,
  optimizedTasks,
  patterns
}: TemplatePrecedenceFormFieldsProps) {
  const selectedPatternId = watch('pattern_id')
  const selectedPredecessorId = watch('predecessor_optimized_task_id')

  const getFilteredTasks = (selectedPatternId: string, excludeTaskId: string = '') => {
    return optimizedTasks.filter(task => 
      task.pattern_id === selectedPatternId && task.optimized_task_id !== excludeTaskId
    )
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Pattern - Required */}
        <div className="space-y-2">
          <Label htmlFor="pattern_id">Job Optimized Pattern *</Label>
          <Select onValueChange={(value) => {
            setValue('pattern_id', value)
            setValue('predecessor_optimized_task_id', '')
            setValue('successor_optimized_task_id', '')
          }}>
            <SelectTrigger>
              <SelectValue placeholder="Select pattern" />
            </SelectTrigger>
            <SelectContent>
              {patterns.map((pattern) => (
                <SelectItem key={pattern.pattern_id} value={pattern.pattern_id}>
                  {pattern.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {!watch('pattern_id') && <p className="text-sm text-red-600">Pattern is required</p>}
        </div>

        {/* Predecessor Task - Required */}
        <div className="space-y-2">
          <Label htmlFor="predecessor_optimized_task_id">Predecessor Task *</Label>
          <Select 
            onValueChange={(value) => setValue('predecessor_optimized_task_id', value)}
            disabled={!selectedPatternId}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select predecessor task" />
            </SelectTrigger>
            <SelectContent>
              {getFilteredTasks(selectedPatternId, selectedPredecessorId).map((task) => (
                <SelectItem key={task.optimized_task_id} value={task.optimized_task_id}>
                  {task.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {!watch('predecessor_optimized_task_id') && selectedPatternId && 
            <p className="text-sm text-red-600">Predecessor task is required</p>}
        </div>

        {/* Successor Task - Required */}
        <div className="space-y-2">
          <Label htmlFor="successor_optimized_task_id">Successor Task *</Label>
          <Select 
            onValueChange={(value) => setValue('successor_optimized_task_id', value)}
            disabled={!selectedPatternId}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select successor task" />
            </SelectTrigger>
            <SelectContent>
              {getFilteredTasks(selectedPatternId, selectedPredecessorId).map((task) => (
                <SelectItem key={task.optimized_task_id} value={task.optimized_task_id}>
                  {task.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {!watch('successor_optimized_task_id') && selectedPatternId && 
            <p className="text-sm text-red-600">Successor task is required</p>}
        </div>

        {/* Min Delay Minutes */}
        <div className="space-y-2">
          <Label htmlFor="min_delay_minutes">Minimum Delay (minutes)</Label>
          <Input
            id="min_delay_minutes"
            type="number"
            min="0"
            {...register('min_delay_minutes', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Minimum delay must be non-negative' }
            })}
          />
          <p className="text-xs text-gray-500">Minimum time between predecessor completion and successor start</p>
          {errors.min_delay_minutes && <p className="text-sm text-red-600">{errors.min_delay_minutes.message}</p>}
        </div>

        {/* Max Delay Minutes */}
        <div className="space-y-2">
          <Label htmlFor="max_delay_minutes">Maximum Delay (minutes)</Label>
          <Input
            id="max_delay_minutes"
            type="number"
            min="0"
            {...register('max_delay_minutes', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Maximum delay must be non-negative' }
            })}
          />
          <p className="text-xs text-gray-500">Maximum time between tasks (0 = no limit)</p>
          {errors.max_delay_minutes && <p className="text-sm text-red-600">{errors.max_delay_minutes.message}</p>}
        </div>

        {/* Transfer Time Minutes */}
        <div className="space-y-2">
          <Label htmlFor="transfer_time_minutes">Transfer Time (minutes)</Label>
          <Input
            id="transfer_time_minutes"
            type="number"
            min="0"
            {...register('transfer_time_minutes', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Transfer time must be non-negative' }
            })}
          />
          <p className="text-xs text-gray-500">Time required for material transfer between departments</p>
          {errors.transfer_time_minutes && <p className="text-sm text-red-600">{errors.transfer_time_minutes.message}</p>}
        </div>
      </div>

      {/* Checkboxes */}
      <div className="flex flex-col space-y-4">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="requires_department_transfer"
            checked={watch('requires_department_transfer')}
            onCheckedChange={(checked) => setValue('requires_department_transfer', checked as boolean)}
          />
          <Label htmlFor="requires_department_transfer">Requires Department Transfer</Label>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-2 pt-4">
        {editingId && (
          <Button type="button" variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={isSubmitting || !watch('pattern_id') || !watch('predecessor_optimized_task_id') || !watch('successor_optimized_task_id')}>
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {editingId ? 'Update' : 'Create'} Template Precedence
        </Button>
      </div>
    </div>
  )
}
