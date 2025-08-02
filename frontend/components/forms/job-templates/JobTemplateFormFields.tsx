"use client"

import { UseFormReturn } from 'react-hook-form'
import { JobTemplateFormData } from '@/lib/schemas'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { FormField, FormSection } from '@/components/forms/common/FormField'
import { Loader2 } from 'lucide-react'

interface JobTemplateFormFieldsProps {
  form: UseFormReturn<JobTemplateFormData>
  onFieldFocus?: (fieldName: string) => void
  defaultSolverParameters?: any
}

export function JobTemplateFormFields({
  form,
  onFieldFocus,
  defaultSolverParameters
}: JobTemplateFormFieldsProps) {
  const { register, formState: { errors, isValidating } } = form

  return (
    <div className="space-y-6">
      <FormSection title="Template Information" description="Basic template configuration">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField
            id="name"
            label="Template Name"
            required
            error={errors.name?.message}
          >
            <Input
              {...register('name')}
              placeholder="e.g., Standard Manufacturing Template"
              onFocus={() => onFieldFocus?.('name')}
            />
          </FormField>

          <FormField
            id="task_count"
            label="Task Count"
            required
            error={errors.task_count?.message}
            description="Number of tasks in this pattern"
          >
            <Input
              type="number"
              min="1"
              {...register('task_count', { valueAsNumber: true })}
              placeholder="1"
              onFocus={() => onFieldFocus?.('task_count')}
            />
          </FormField>

          <FormField
            id="total_min_duration_minutes"
            label="Total Min Duration (minutes)"
            error={errors.total_min_duration_minutes?.message}
            description="Sum of minimum task durations"
          >
            <Input
              type="number"
              min="0"
              {...register('total_min_duration_minutes', { valueAsNumber: true })}
              placeholder="60"
              onFocus={() => onFieldFocus?.('total_min_duration_minutes')}
            />
          </FormField>

          <FormField
            id="critical_path_length_minutes"
            label="Critical Path Length (minutes)"
            error={errors.critical_path_length_minutes?.message}
            description="Minimum time to complete pattern (longest path)"
          >
            <Input
              type="number"
              min="0"
              {...register('critical_path_length_minutes', { valueAsNumber: true })}
              placeholder="60"
              onFocus={() => onFieldFocus?.('critical_path_length_minutes')}
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
            placeholder="Template description and use cases"
            rows={3}
            onFocus={() => onFieldFocus?.('description')}
          />
        </FormField>
      </FormSection>

      <FormSection 
        title="Solver Configuration" 
        description="Configure CP-SAT solver parameters for optimal performance"
      >
        <FormField
          id="solver_parameters"
          label="Blessed Solver Parameters (JSON)"
          required
          error={errors.solver_parameters?.message}
          description={
            <span>
              Configure CP-SAT solver parameters for optimal performance. Default values shown are production-tested.
              {isValidating && (
                <span className="flex items-center text-xs text-blue-600 mt-1">
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                  Validating parameters...
                </span>
              )}
            </span>
          }
        >
          <Textarea
            {...register('solver_parameters')}
            rows={8}
            className="font-mono text-sm"
            placeholder={JSON.stringify(defaultSolverParameters, null, 2)}
            onFocus={() => onFieldFocus?.('solver_parameters')}
          />
        </FormField>
      </FormSection>
    </div>
  )
}