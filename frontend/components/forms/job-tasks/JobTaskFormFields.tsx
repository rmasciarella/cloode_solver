"use client"

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2 } from 'lucide-react'

type JobInstance = {
  instance_id: string
  name: string
  template_id: string
}

type TemplateTask = {
  template_task_id: string
  name: string
  template_id: string
}

type TemplateTaskMode = {
  template_task_mode_id: string
  mode_name: string
  duration_minutes: number
}

type Machine = {
  machine_resource_id: string
  name: string
}

interface JobTaskFormFieldsProps {
  registerWithPerformance: (name: string, validation?: any) => any
  setValue: (name: string, value: any) => void
  watch: (name?: string) => any
  errors: any
  editingId: string | null
  isSubmitting: boolean
  handleCancel: () => void
  jobInstances: JobInstance[]
  templateTasks: TemplateTask[]
  taskModes: TemplateTaskMode[]
  machines: Machine[]
  performanceTracker: any
}

export function JobTaskFormFields({
  registerWithPerformance,
  setValue,
  watch,
  errors,
  editingId,
  isSubmitting,
  handleCancel,
  jobInstances,
  templateTasks,
  taskModes,
  machines,
  performanceTracker
}: JobTaskFormFieldsProps) {
  const selectedInstanceId = watch('instance_id')
  const selectedTaskId = watch('template_task_id')

  const getFilteredTasks = (instanceId: string) => {
    const instance = jobInstances.find(inst => inst.instance_id === instanceId)
    if (!instance) return []
    
    return templateTasks.filter(task => task.template_id === instance.template_id)
  }

  const getFilteredModes = (taskId: string) => {
    return taskModes.filter(mode => (mode as any).template_task_id === taskId)
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Job Instance - Required */}
        <div className="space-y-2">
          <Label htmlFor="instance_id">Job Instance *</Label>
          <Select onValueChange={(value) => {
            performanceTracker.startValidation('instance_id')
            setValue('instance_id', value)
            setValue('template_task_id', '')
            setValue('selected_mode_id', '')
            performanceTracker.trackInteraction('click', 'instance_id')
            performanceTracker.trackValidation('instance_id', !value)
          }}>
            <SelectTrigger
              onFocus={() => performanceTracker.trackInteraction('focus', 'instance_id')}
              onClick={() => performanceTracker.trackInteraction('click', 'instance_id')}
            >
              <SelectValue placeholder="Select job instance" />
            </SelectTrigger>
            <SelectContent>
              {jobInstances.map((instance) => (
                <SelectItem key={instance.instance_id} value={instance.instance_id}>
                  {instance.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {!watch('instance_id') && <p className="text-sm text-red-600">Job instance is required</p>}
        </div>

        {/* Template Task - Required */}
        <div className="space-y-2">
          <Label htmlFor="template_task_id">Template Task *</Label>
          <Select 
            onValueChange={(value) => {
              performanceTracker.startValidation('template_task_id')
              setValue('template_task_id', value)
              setValue('selected_mode_id', '')
              performanceTracker.trackInteraction('click', 'template_task_id')
              performanceTracker.trackValidation('template_task_id', !value)
            }}
            disabled={!selectedInstanceId}
          >
            <SelectTrigger
              onFocus={() => performanceTracker.trackInteraction('focus', 'template_task_id')}
              onClick={() => performanceTracker.trackInteraction('click', 'template_task_id')}
            >
              <SelectValue placeholder="Select template task" />
            </SelectTrigger>
            <SelectContent>
              {getFilteredTasks(selectedInstanceId).map((task) => (
                <SelectItem key={task.template_task_id} value={task.template_task_id}>
                  {task.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {!watch('template_task_id') && selectedInstanceId && 
            <p className="text-sm text-red-600">Template task is required</p>}
        </div>

        {/* Task Mode */}
        <div className="space-y-2">
          <Label htmlFor="selected_mode_id">Task Mode</Label>
          <Select 
            onValueChange={(value) => setValue('selected_mode_id', value)}
            disabled={!selectedTaskId}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select task mode" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No Specific Mode</SelectItem>
              {getFilteredModes(selectedTaskId).map((mode) => (
                <SelectItem key={mode.template_task_mode_id} value={mode.template_task_mode_id}>
                  {mode.mode_name} ({mode.duration_minutes}m)
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Assigned Machine */}
        <div className="space-y-2">
          <Label htmlFor="assigned_machine_id">Assigned Machine</Label>
          <Select onValueChange={(value) => setValue('assigned_machine_id', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select machine" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No Machine Assignment</SelectItem>
              {machines.map((machine) => (
                <SelectItem key={machine.machine_resource_id} value={machine.machine_resource_id}>
                  {machine.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Start Time Minutes */}
        <div className="space-y-2">
          <Label htmlFor="start_time_minutes">Start Time (minutes)</Label>
          <Input
            id="start_time_minutes"
            type="number"
            min="0"
            {...registerWithPerformance('start_time_minutes', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Start time must be non-negative' }
            })}
          />
          <p className="text-xs text-gray-500">Time from schedule start in minutes</p>
          {errors.start_time_minutes && <p className="text-sm text-red-600">{errors.start_time_minutes.message}</p>}
        </div>

        {/* End Time Minutes */}
        <div className="space-y-2">
          <Label htmlFor="end_time_minutes">End Time (minutes)</Label>
          <Input
            id="end_time_minutes"
            type="number"
            min="0"
            {...registerWithPerformance('end_time_minutes', { 
              valueAsNumber: true,
              min: { value: 0, message: 'End time must be non-negative' }
            })}
          />
          <p className="text-xs text-gray-500">Task completion time in minutes</p>
          {errors.end_time_minutes && <p className="text-sm text-red-600">{errors.end_time_minutes.message}</p>}
        </div>

        {/* Actual Duration Minutes */}
        <div className="space-y-2">
          <Label htmlFor="actual_duration_minutes">Actual Duration (minutes)</Label>
          <Input
            id="actual_duration_minutes"
            type="number"
            min="0"
            {...registerWithPerformance('actual_duration_minutes', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Duration must be non-negative' }
            })}
          />
          <p className="text-xs text-gray-500">Actual time taken to complete task</p>
          {errors.actual_duration_minutes && <p className="text-sm text-red-600">{errors.actual_duration_minutes.message}</p>}
        </div>

        {/* Setup Time Minutes */}
        <div className="space-y-2">
          <Label htmlFor="setup_time_minutes">Setup Time (minutes)</Label>
          <Input
            id="setup_time_minutes"
            type="number"
            min="0"
            {...registerWithPerformance('setup_time_minutes', { 
              valueAsNumber: true,
              min: { value: 0, message: 'Setup time must be non-negative' }
            })}
          />
          <p className="text-xs text-gray-500">Time required for task setup</p>
          {errors.setup_time_minutes && <p className="text-sm text-red-600">{errors.setup_time_minutes.message}</p>}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-2 pt-4">
        {editingId && (
          <Button 
            type="button" 
            variant="outline" 
            onClick={() => {
              performanceTracker.trackInteraction('click', 'cancel_button')
              handleCancel()
            }}
          >
            Cancel
          </Button>
        )}
        <Button 
          type="submit" 
          disabled={isSubmitting || !watch('instance_id') || !watch('template_task_id')}
          onClick={() => performanceTracker.trackInteraction('click', 'submit_button')}
        >
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {editingId ? 'Update' : 'Create'} Job Task
        </Button>
      </div>
    </div>
  )
}
