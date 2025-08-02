"use client"

import { UseFormReturn } from 'react-hook-form'
import { FormField, FormSection } from '@/components/forms/common/FormField'
import { Input } from '@/components/ui/input'
// import { Textarea } from '@/components/ui/textarea' // AGENT-1: Removed unused import
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { InfoIcon } from 'lucide-react'

// Import the form data type from parent
interface SetupTimeFormData {
  from_optimized_task_id: string
  to_optimized_task_id: string
  machine_resource_id: string
  setup_time_minutes: number
  setup_type: string
  complexity_level: string
  requires_operator_skill: string
  requires_certification: boolean
  requires_supervisor_approval: boolean
  setup_cost: number
  efficiency_impact_percent: number
  product_family_from: string
  product_family_to: string
}

interface SetupTimeFormFieldsProps {
  form: UseFormReturn<SetupTimeFormData>
  optimizedTasks: Array<{ 
    optimized_task_id: string
    task_name: string
    pattern_name: string
    pattern_id: string
  }>
  machines: Array<{ 
    machine_resource_id: string
    name: string
    code: string
    setup_time_minutes: number
  }>
  groupedTasks: Record<string, Array<{
    optimized_task_id: string
    task_name: string
    pattern_name: string
    pattern_id: string
  }>>
  onFieldFocus?: (fieldName: string) => void | undefined
  onInteraction?: () => void | undefined
}

export function SetupTimeFormFields({ 
  form, 
  _optimizedTasks,
  machines,
  groupedTasks,
  onFieldFocus, 
  onInteraction 
}: SetupTimeFormFieldsProps) {
  const { register, formState: { errors }, watch, setValue } = form
  const fromTaskId = watch('from_optimized_task_id')
  const toTaskId = watch('to_optimized_task_id')
  const machineId = watch('machine_resource_id')

  const handleFieldFocus = (fieldName: string) => {
    onFieldFocus?.(fieldName)
    onInteraction?.()
  }

  // Get selected machine's default setup time
  const selectedMachine = machines.find(m => m.machine_resource_id === machineId)
  const defaultSetupTime = selectedMachine?.setup_time_minutes || 0

  return (
    <div className="space-y-6">
      <Alert>
        <InfoIcon className="h-4 w-4" />
        <AlertDescription>
          Setup times define the transition time required when changing from one task to another on a specific machine.
          This includes tool changes, material changes, cleaning, and calibration.
        </AlertDescription>
      </Alert>

      <FormSection title="Task Transition" description="Select the source and target tasks for this setup">
        <div className="grid grid-cols-2 gap-4">
          <FormField 
            id="from_optimized_task_id" 
            label="From Task" 
            required 
            error={errors.from_optimized_task_id?.message}
            description="The task that completes before setup"
          >
            <Select
              value={fromTaskId || ''}
              onValueChange={(value) => {
                setValue('from_optimized_task_id', value)
                onInteraction?.()
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select source task" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(groupedTasks).map(([patternName, tasks]) => (
                  <div key={patternName}>
                    <div className="px-2 py-1 text-sm font-medium text-gray-500">
                      {patternName}
                    </div>
                    {tasks.map(task => (
                      <SelectItem 
                        key={task.optimized_task_id} 
                        value={task.optimized_task_id}
                        disabled={task.optimized_task_id === toTaskId}
                      >
                        {task.task_name}
                      </SelectItem>
                    ))}
                  </div>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField 
            id="to_optimized_task_id" 
            label="To Task" 
            required 
            error={errors.to_optimized_task_id?.message}
            description="The task that starts after setup"
          >
            <Select
              value={toTaskId || ''}
              onValueChange={(value) => {
                setValue('to_optimized_task_id', value)
                onInteraction?.()
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select target task" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(groupedTasks).map(([patternName, tasks]) => (
                  <div key={patternName}>
                    <div className="px-2 py-1 text-sm font-medium text-gray-500">
                      {patternName}
                    </div>
                    {tasks.map(task => (
                      <SelectItem 
                        key={task.optimized_task_id} 
                        value={task.optimized_task_id}
                        disabled={task.optimized_task_id === fromTaskId}
                      >
                        {task.task_name}
                      </SelectItem>
                    ))}
                  </div>
                ))}
              </SelectContent>
            </Select>
          </FormField>
        </div>
      </FormSection>

      <FormSection title="Machine & Duration" description="Configure the machine and setup duration">
        <div className="grid grid-cols-2 gap-4">
          <FormField 
            id="machine_resource_id" 
            label="Machine" 
            required 
            error={errors.machine_resource_id?.message}
            description="The machine where this setup occurs"
          >
            <Select
              value={machineId || ''}
              onValueChange={(value) => {
                setValue('machine_resource_id', value)
                // Auto-populate setup time with machine's default
                const machine = machines.find(m => m.machine_resource_id === value)
                if (machine && !watch('setup_time_minutes')) {
                  setValue('setup_time_minutes', machine.setup_time_minutes)
                }
                onInteraction?.()
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select machine" />
              </SelectTrigger>
              <SelectContent>
                {machines.map(machine => (
                  <SelectItem key={machine.machine_resource_id} value={machine.machine_resource_id}>
                    {machine.name} ({machine.code}) - Default: {machine.setup_time_minutes} min
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>

          <FormField 
            id="setup_time_minutes" 
            label="Setup Time (minutes)" 
            required 
            error={errors.setup_time_minutes?.message}
            description={defaultSetupTime ? `Machine default: ${defaultSetupTime} min` : "Time required for setup"}
          >
            <Input
              type="number"
              {...register('setup_time_minutes', { 
                required: 'Setup time is required',
                min: { value: 0, message: 'Must be 0 or greater' }
              })}
              onFocus={() => handleFieldFocus('setup_time_minutes')}
              placeholder={defaultSetupTime ? `Default: ${defaultSetupTime}` : "0"}
            />
          </FormField>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <FormField 
            id="setup_type" 
            label="Setup Type" 
            required 
            error={errors.setup_type?.message}
            description="Type of setup required"
          >
            <Select
              value={watch('setup_type') || ''}
              onValueChange={(value) => {
                setValue('setup_type', value)
                onInteraction?.()
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select setup type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="standard">Standard</SelectItem>
                <SelectItem value="complex">Complex</SelectItem>
                <SelectItem value="quick">Quick Change</SelectItem>
                <SelectItem value="full">Full Changeover</SelectItem>
              </SelectContent>
            </Select>
          </FormField>

          <FormField 
            id="complexity_level" 
            label="Complexity Level" 
            required 
            error={errors.complexity_level?.message}
            description="Complexity of the setup"
          >
            <Select
              value={watch('complexity_level') || ''}
              onValueChange={(value) => {
                setValue('complexity_level', value)
                onInteraction?.()
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select complexity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="very_high">Very High</SelectItem>
              </SelectContent>
            </Select>
          </FormField>
        </div>
      </FormSection>

      <FormSection title="Advanced Settings" description="Additional setup configuration">
        <div className="grid grid-cols-2 gap-4">
          <FormField 
            id="setup_cost" 
            label="Setup Cost ($)" 
            required 
            error={errors.setup_cost?.message}
            description="Cost associated with this setup"
          >
            <Input
              type="number"
              step="0.01"
              {...register('setup_cost', { 
                required: 'Setup cost is required',
                min: { value: 0, message: 'Must be 0 or greater' }
              })}
              onFocus={() => handleFieldFocus('setup_cost')}
              placeholder="0.00"
            />
          </FormField>

          <FormField 
            id="efficiency_impact_percent" 
            label="Efficiency Impact (%)" 
            required 
            error={errors.efficiency_impact_percent?.message}
            description="Impact on production efficiency"
          >
            <Input
              type="number"
              {...register('efficiency_impact_percent', { 
                required: 'Efficiency impact is required',
                min: { value: 0, message: 'Must be 0 or greater' },
                max: { value: 100, message: 'Must be 100 or less' }
              })}
              onFocus={() => handleFieldFocus('efficiency_impact_percent')}
              placeholder="0"
            />
          </FormField>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <FormField 
            id="product_family_from" 
            label="From Product Family" 
            error={errors.product_family_from?.message}
            description="Product family of source task"
          >
            <Input
              {...register('product_family_from')}
              onFocus={() => handleFieldFocus('product_family_from')}
              placeholder="e.g., Series A"
            />
          </FormField>

          <FormField 
            id="product_family_to" 
            label="To Product Family" 
            error={errors.product_family_to?.message}
            description="Product family of target task"
          >
            <Input
              {...register('product_family_to')}
              onFocus={() => handleFieldFocus('product_family_to')}
              placeholder="e.g., Series B"
            />
          </FormField>
        </div>

        <FormField 
          id="requires_operator_skill" 
          label="Required Operator Skill" 
          error={errors.requires_operator_skill?.message}
          description="Specific skill required for this setup"
        >
          <Input
            {...register('requires_operator_skill')}
            onFocus={() => handleFieldFocus('requires_operator_skill')}
            placeholder="e.g., CNC Programming, Advanced Calibration"
          />
        </FormField>

        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="requires_certification"
              checked={watch('requires_certification')}
              onCheckedChange={(checked) => {
                setValue('requires_certification', checked as boolean)
                onInteraction?.()
              }}
            />
            <label 
              htmlFor="requires_certification"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Requires Certification
            </label>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="requires_supervisor_approval"
              checked={watch('requires_supervisor_approval')}
              onCheckedChange={(checked) => {
                setValue('requires_supervisor_approval', checked as boolean)
                onInteraction?.()
              }}
            />
            <label 
              htmlFor="requires_supervisor_approval"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Requires Supervisor Approval
            </label>
          </div>
        </div>
      </FormSection>
    </div>
  )
}