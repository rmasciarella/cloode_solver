"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { jobTemplateService } from '@/lib/services'
import { jobTemplateFormSchema, type JobTemplateFormData } from '@/lib/schemas'
import { useToast } from '@/hooks/use-toast'
import { useFormSubmission } from './useFormSubmission'
import { useFormPerformance } from '@/lib/hooks/use-form-performance'

const defaultSolverParameters = {
  "num_search_workers": 8,
  "max_time_in_seconds": 60,
  "linearization_level": 1,
  "search_branching": "FIXED_SEARCH",
  "cp_model_presolve": true,
  "repair_hint": true
}

export function useJobTemplateForm(
  onSuccess?: () => void,
  editingId?: string | null
) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()
  const performanceTracker = useFormPerformance('job-template-form')

  const form = useForm<JobTemplateFormData>({
    resolver: zodResolver(jobTemplateFormSchema),
    defaultValues: {
      name: '',
      description: '',
      solver_parameters: JSON.stringify(defaultSolverParameters, null, 2),
      task_count: 1,
      total_min_duration_minutes: 60,
      critical_path_length_minutes: 60
    }
  })

  const { handleSubmit: handleFormSubmit } = useFormSubmission({
    onSubmit: async (data: JobTemplateFormData) => {
      performanceTracker.trackSubmissionStart()
      setIsSubmitting(true)
      
      try {
        // Track validation start time
        performanceTracker.startValidation('solver_parameters')
        
        // Validate solver parameters using the service
        const validationResponse = await jobTemplateService.validateSolverParameters(data.solver_parameters)
        
        // Track validation time
        performanceTracker.trackValidation('solver_parameters', !validationResponse.success)
        
        if (!validationResponse.success) {
          toast({
            title: "Error",
            description: validationResponse.error || "Invalid solver parameters",
            variant: "destructive"
          })
          performanceTracker.trackSubmissionEnd(false)
          return
        }

        const formData = {
          name: data.name,
          description: data.description || null,
          solver_parameters: data.solver_parameters, // Already parsed by Zod schema
          task_count: data.task_count,
          total_min_duration_minutes: data.total_min_duration_minutes,
          critical_path_length_minutes: data.critical_path_length_minutes
        }

        let response
        
        if (editingId) {
          response = await jobTemplateService.update(editingId, formData)
        } else {
          response = await jobTemplateService.create(formData)
        }
        
        if (response.success) {
          toast({
            title: "Success",
            description: `Job template ${editingId ? 'updated' : 'created'} successfully`
          })
          form.reset()
          performanceTracker.trackSubmissionEnd(true)
          onSuccess?.()
        } else {
          console.error('Error saving job template:', response.error)
          toast({
            title: "Error",
            description: response.error || "Failed to save job template",
            variant: "destructive"
          })
          performanceTracker.trackSubmissionEnd(false)
        }
      } catch (error) {
        console.error('Error in form submission:', error)
        performanceTracker.trackSubmissionEnd(false)
        toast({
          title: "Error",
          description: "An unexpected error occurred",
          variant: "destructive"
        })
      } finally {
        setIsSubmitting(false)
      }
    },
    onSuccess,
    submissionTime: 2000
  })

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete the job template "${name}"?`)) return
    
    performanceTracker.trackInteraction('click', 'delete_template')

    try {
      const response = await jobTemplateService.delete(id)
      
      if (response.success) {
        toast({
          title: "Success",
          description: "Job template deleted successfully"
        })
        onSuccess?.()
      } else {
        console.error('Error deleting job template:', response.error)
        toast({
          title: "Error",
          description: response.error || "Failed to delete job template",
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Error in handleDelete:', error)
      toast({
        title: "Error",
        description: "An unexpected error occurred",
        variant: "destructive"
      })
    }
  }

  const handleToggleActive = async (id: string, name: string, isActive: boolean) => {
    performanceTracker.trackInteraction('click', 'toggle_active')
    
    try {
      const response = await jobTemplateService.update(id, { is_active: !isActive })
      
      if (response.success) {
        toast({
          title: "Success",
          description: `Job template "${name}" ${!isActive ? 'activated' : 'deactivated'} successfully`
        })
        onSuccess?.()
      } else {
        toast({
          title: "Error",
          description: response.error || "Failed to update job template",
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Error in handleToggleActive:', error)
      toast({
        title: "Error",
        description: "An unexpected error occurred",
        variant: "destructive"
      })
    }
  }

  return {
    form,
    isSubmitting,
    handleSubmit: form.handleSubmit(handleFormSubmit),
    handleDelete,
    handleToggleActive,
    performanceTracker,
    defaultSolverParameters
  }
}