"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { sequenceResourceService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'
import { useFormSubmission } from './useFormSubmission'
import { z } from 'zod'

// Define the form schema
const sequenceResourceFormSchema = z.object({
  sequence_id: z.string().min(1, "Sequence ID is required"),
  name: z.string().min(1, "Name is required").max(255, "Name must be 255 characters or less"),
  description: z.string().optional(),
  department_id: z.string().optional(),
  setup_time_minutes: z.number().min(0, "Setup time must be non-negative"),
  teardown_time_minutes: z.number().min(0, "Teardown time must be non-negative"),
  max_concurrent_jobs: z.number().min(1, "Max concurrent jobs must be at least 1"),
  resource_type: z.enum(['exclusive', 'shared', 'pooled']),
  priority: z.number().min(1, "Priority must be at least 1"),
  is_active: z.boolean()
})

export type SequenceResourceFormData = z.infer<typeof sequenceResourceFormSchema>

export function useSequenceResourceForm(
  onSuccess?: () => void,
  editingId?: string | null
) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const form = useForm<SequenceResourceFormData>({
    resolver: zodResolver(sequenceResourceFormSchema),
    defaultValues: {
      sequence_id: '',
      name: '',
      description: '',
      department_id: '',
      setup_time_minutes: 0,
      teardown_time_minutes: 0,
      max_concurrent_jobs: 1,
      resource_type: 'exclusive',
      priority: 1,
      is_active: true
    }
  })

  const { handleSubmit: handleFormSubmit } = useFormSubmission({
    onSubmit: async (data: SequenceResourceFormData) => {
      setIsSubmitting(true)
      
      try {
        const formData = {
          sequence_id: data.sequence_id,
          name: data.name,
          description: data.description || null,
          department_id: data.department_id === 'none' ? null : data.department_id || null,
          setup_time_minutes: data.setup_time_minutes,
          teardown_time_minutes: data.teardown_time_minutes,
          max_concurrent_jobs: data.max_concurrent_jobs,
          resource_type: data.resource_type,
          priority: data.priority,
          is_active: data.is_active
        }

        let response
        if (editingId) {
          response = await sequenceResourceService.update(editingId, formData)
        } else {
          response = await sequenceResourceService.create(formData)
        }

        if (response.success) {
          toast({
            title: "Success",
            description: `Sequence resource ${editingId ? 'updated' : 'created'} successfully`
          })
          form.reset()
          onSuccess?.()
        } else {
          // Handle specific database errors
          let errorMessage = response.error || "Failed to save sequence resource"
          if (response.error?.includes('duplicate key value violates unique constraint') && 
              response.error?.includes('sequence_id')) {
            errorMessage = `Sequence ID "${data.sequence_id}" already exists. Please use a different ID.`
          }
          
          toast({
            title: "Error",
            description: errorMessage,
            variant: "destructive"
          })
        }
      } catch (error) {
        console.error('Error in onSubmit:', error)
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
    if (!confirm(`Are you sure you want to delete "${name}"?\n\nThis action cannot be undone.`)) return

    const response = await sequenceResourceService.delete(id)
    
    if (response.success) {
      toast({
        title: "Success",
        description: `Sequence resource "${name}" deleted successfully`
      })
      onSuccess?.()
    } else {
      let errorMessage = response.error || "Failed to delete sequence resource"
      let errorDetails = ""
      
      // Check for common constraint violation errors
      if (response.error?.includes('foreign key constraint') || 
          response.error?.includes('violates foreign key')) {
        errorMessage = "Cannot delete sequence resource - it's still in use"
        errorDetails = "This sequence resource has related records. Either delete those first or deactivate this resource instead."
      }

      toast({
        title: "Error",
        description: errorDetails || errorMessage,
        variant: "destructive"
      })
    }
  }

  const handleToggleActive = async (id: string, name: string, isActive: boolean) => {
    const newStatus = !isActive
    const action = newStatus ? 'reactivate' : 'deactivate'
    
    if (!confirm(`Are you sure you want to ${action} "${name}"?`)) return

    const response = await sequenceResourceService.toggleActive(id)
    
    if (response.success) {
      toast({
        title: "Success",
        description: `Sequence resource "${name}" ${newStatus ? 'reactivated' : 'deactivated'} successfully`
      })
      onSuccess?.()
    } else {
      toast({
        title: "Error",
        description: response.error || `Failed to ${action} sequence resource`,
        variant: "destructive"
      })
    }
  }

  return {
    form,
    isSubmitting,
    handleSubmit: form.handleSubmit(handleFormSubmit),
    handleDelete,
    handleToggleActive
  }
}
