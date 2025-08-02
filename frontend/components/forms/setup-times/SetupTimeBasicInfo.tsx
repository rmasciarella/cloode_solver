import { UseFormReturn } from 'react-hook-form'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { SetupTimeFormData } from '@/lib/schemas/setup-time.schema'
import type { OptimizedTask, Machine } from '@/hooks/forms/useSetupTimeData'

interface SetupTimeBasicInfoProps {
  form: UseFormReturn<SetupTimeFormData>
  templateTasks: OptimizedTask[]
  machines: Machine[]
  onFieldFocus: (fieldId: string) => void
  onFieldBlur: (fieldId: string, value: any) => void
  onFieldChange: (fieldId: string, value: any) => void
}

export function SetupTimeBasicInfo({
  form,
  templateTasks,
  machines,
  onFieldFocus,
  onFieldBlur,
  onFieldChange
}: SetupTimeBasicInfoProps) {
  const { register, setValue, watch, formState: { errors } } = form

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label htmlFor="from_optimized_task_id">From Template Task *</Label>
        <Select 
          value={watch('from_optimized_task_id')}
          onValueChange={(value) => {
            setValue('from_optimized_task_id', value)
            onFieldChange('from_optimized_task_id', value)
          }}
          onOpenChange={(open) => {
            if (open) onFieldFocus('from_optimized_task_id')
            else onFieldBlur('from_optimized_task_id', watch('from_optimized_task_id'))
          }}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select from task" />
          </SelectTrigger>
          <SelectContent>
            {templateTasks.map((task) => (
              <SelectItem key={task.optimized_task_id} value={task.optimized_task_id}>
                {task.pattern_name} - {task.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.from_optimized_task_id && (
          <p className="text-sm text-red-600">{errors.from_optimized_task_id.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="to_optimized_task_id">To Template Task *</Label>
        <Select 
          value={watch('to_optimized_task_id')}
          onValueChange={(value) => {
            setValue('to_optimized_task_id', value)
            onFieldChange('to_optimized_task_id', value)
          }}
          onOpenChange={(open) => {
            if (open) onFieldFocus('to_optimized_task_id')
            else onFieldBlur('to_optimized_task_id', watch('to_optimized_task_id'))
          }}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select to task" />
          </SelectTrigger>
          <SelectContent>
            {templateTasks
              .filter(task => task.optimized_task_id !== watch('from_optimized_task_id'))
              .map((task) => (
                <SelectItem key={task.optimized_task_id} value={task.optimized_task_id}>
                  {task.pattern_name} - {task.name}
                </SelectItem>
              ))}
          </SelectContent>
        </Select>
        {errors.to_optimized_task_id && (
          <p className="text-sm text-red-600">{errors.to_optimized_task_id.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="machine_resource_id">Machine *</Label>
        <Select 
          value={watch('machine_resource_id')}
          onValueChange={(value) => {
            setValue('machine_resource_id', value)
            onFieldChange('machine_resource_id', value)
          }}
          onOpenChange={(open) => {
            if (open) onFieldFocus('machine_resource_id')
            else onFieldBlur('machine_resource_id', watch('machine_resource_id'))
          }}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select machine" />
          </SelectTrigger>
          <SelectContent>
            {machines.map((machine) => (
              <SelectItem key={machine.machine_resource_id} value={machine.machine_resource_id}>
                {machine.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.machine_resource_id && (
          <p className="text-sm text-red-600">{errors.machine_resource_id.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="setup_time_minutes">Setup Time (minutes) *</Label>
        <Input
          id="setup_time_minutes"
          type="number"
          min="0"
          {...register('setup_time_minutes', { valueAsNumber: true })}
          onFocus={() => onFieldFocus('setup_time_minutes')}
          onBlur={(e) => onFieldBlur('setup_time_minutes', parseFloat(e.target.value) || 0)}
          onChange={(e) => onFieldChange('setup_time_minutes', parseFloat(e.target.value) || 0)}
        />
        {errors.setup_time_minutes && (
          <p className="text-sm text-red-600">{errors.setup_time_minutes.message}</p>
        )}
      </div>
    </div>
  )
}