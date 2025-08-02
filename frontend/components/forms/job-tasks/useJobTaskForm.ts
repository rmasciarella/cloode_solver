"use client"

import { useState, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { instanceTaskAssignmentService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'
import { handleFormError, logUnmappedError } from '@/lib/utils/error-mapping'
import { useFormPerformance } from '@/lib/hooks/use-form-performance'

type JobTask = {
  task_id: string
  instance_id: string
  template_task_id: string
  selected_mode_id: string | null
  assigned_machine_id: string | null
  start_time_minutes: number | null
  end_time_minutes: number | null
  actual_duration_minutes: number | null
  setup_time_minutes: number
  created_at: string
}

type JobTaskFormData = {
  instance_id: string
  template_task_id: string
  selected_mode_id: string
  assigned_machine_id: string
  start_time_minutes: number
  end_time_minutes: number
  actual_duration_minutes: number
  setup_time_minutes: number
}

export function useJobTaskForm(fetchJobTasks: () => void) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()
  
  // Performance monitoring with standardized hook
  const performanceTracker = useFormPerformance('job-task-form')

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<JobTaskFormData>({
    defaultValues: {
      instance_id: '',
      template_task_id: '',
      selected_mode_id: '',
      assigned_machine_id: '',
      start_time_minutes: 0,
      end_time_minutes: 0,
      actual_duration_minutes: 0,
      setup_time_minutes: 0
    }
  })

  // Enhanced register function with performance tracking
  const registerWithPerformance = useCallback((name: keyof JobTaskFormData, validation?: any) => {
    return {
      ...register(name, validation),
      onFocus: (_e: any) => {
        performanceTracker.trackInteraction('focus', name)
        // React Hook Form doesn't provide onFocus, handle manually
      },
      onBlur: (_e: any) => {
        // Track field validation
        performanceTracker.startValidation(name)
        
        // Let react-hook-form handle validation
        const hasError = !!errors[name]
        performanceTracker.trackValidation(name, hasError)
        
        // Call original onBlur if it exists
        register(name, validation).onBlur?.(_e)
      },
      onChange: (_e: any) => {
        performanceTracker.trackInteraction('change', name)
        register(name, validation).onChange?.(_e)
      }
    }
  }, [register, performanceTracker, errors])

  const onSubmit = async (data: JobTaskFormData) => {
    setIsSubmitting(true)
    performanceTracker.trackSubmissionStart()
    
    try {
      // Validate business logic
      performanceTracker.startValidation('time_validation')
      if (data.start_time_minutes >= data.end_time_minutes) {
        performanceTracker.trackValidation('time_validation', true, 'End time must be after start time')
        toast({
          title: "Error",
          description: "End time must be after start time",
          variant: "destructive"
        })
        performanceTracker.trackSubmissionEnd(false)
        setIsSubmitting(false)
        return
      }
      performanceTracker.trackValidation('time_validation', false)

      const formData = {
        instance_id: data.instance_id,
        template_task_id: data.template_task_id,
        selected_mode_id: data.selected_mode_id || null,
        assigned_machine_id: data.assigned_machine_id || null,
        start_time_minutes: data.start_time_minutes || null,
        end_time_minutes: data.end_time_minutes || null,
        actual_duration_minutes: data.actual_duration_minutes || null,
        setup_time_minutes: data.setup_time_minutes
      }

      // TODO: Cannot use instanceTaskAssignmentService because it expects different fields
      // The JobTask type doesn't match InstanceTaskAssignment type
      // Need to either create a proper job-task service or map the data correctly
      
      // Temporarily show error message to user
      toast({
        title: "Not Implemented",
        description: "Job task management is not yet implemented. The required database table and service are missing.",
        variant: "destructive"
      })
      
      // Original code commented out due to type mismatch:
      // if (editingId) {
      //   const response = await instanceTaskAssignmentService.update(editingId, formData)
      //   if (!response.success) {
      //     throw new Error(response.error || 'Failed to update job task')
      //   }
      //   toast({
      //     title: "Success",
      //     description: "Job task updated successfully"
      //   })
      // } else {
      //   const response = await instanceTaskAssignmentService.create(formData)
      //   if (!response.success) {
      //     throw new Error(response.error || 'Failed to create job task')
      //   }
      //   toast({
      //     title: "Success",
      //     description: "Job task created successfully"
      //   })
      // }

      reset()
      setEditingId(null)
      fetchJobTasks()
      performanceTracker.trackSubmissionEnd(true)
    } catch (error) {
      console.error('Error saving job task:', error)
      logUnmappedError(error, 'saveJobTask')
      performanceTracker.trackSubmissionEnd(false)
      const errorInfo = handleFormError(error, 'job task', editingId ? 'update' : 'create')
      toast(errorInfo)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = useCallback((task: JobTask) => {
    setEditingId(task.task_id)
    setValue('instance_id', task.instance_id)
    setValue('template_task_id', task.template_task_id)
    setValue('selected_mode_id', task.selected_mode_id || '')
    setValue('assigned_machine_id', task.assigned_machine_id || '')
    setValue('start_time_minutes', task.start_time_minutes || 0)
    setValue('end_time_minutes', task.end_time_minutes || 0)
    setValue('actual_duration_minutes', task.actual_duration_minutes || 0)
    setValue('setup_time_minutes', task.setup_time_minutes)
  }, [setValue])

  const handleDelete = useCallback(async (id: string) => {
    if (!confirm('Are you sure you want to delete this job task assignment?')) return

    try {
      const response = await instanceTaskAssignmentService.delete(id)

      if (!response.success) {
        throw new Error(response.error || 'Failed to delete job task')
      }

      toast({
        title: "Success",
        description: "Job task deleted successfully"
      })
      fetchJobTasks()
    } catch (error) {
      console.error('Error deleting job task:', error)
      logUnmappedError(error, 'deleteJobTask')
      const errorInfo = handleFormError(error, 'job task', 'delete')
      toast(errorInfo)
    }
  }, [toast, fetchJobTasks])

  const handleCancel = useCallback(() => {
    reset()
    setEditingId(null)
  }, [reset])

  return {
    register,
    registerWithPerformance,
    handleSubmit,
    setValue,
    watch,
    errors,
    editingId,
    isSubmitting,
    onSubmit,
    handleEdit,
    handleDelete,
    handleCancel,
    performanceTracker
  }
}
