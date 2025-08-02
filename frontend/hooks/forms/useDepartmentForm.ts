"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { departmentService } from '@/lib/services'
import { departmentFormSchema, type DepartmentFormData } from '@/lib/schemas'
import { useToast } from '@/hooks/use-toast'
import { useFormSubmission } from './useFormSubmission'

export function useDepartmentForm(
  onSuccess?: () => void,
  editingId?: string | null
) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const form = useForm<DepartmentFormData>({
    resolver: zodResolver(departmentFormSchema),
    defaultValues: {
      code: '',
      name: '',
      description: '',
      parent_department_id: '',
      cost_center: '',
      default_shift_start: 32, // 8 AM
      default_shift_end: 64,   // 4 PM
      overtime_allowed: true,
      is_active: true
    }
  })

  const { handleSubmit: handleFormSubmit } = useFormSubmission({
    onSubmit: async (data: DepartmentFormData) => {
      setIsSubmitting(true)
      
      try {
        // Ensure required fields are present
        const submitData = {
          ...data,
          code: data.code || '',
          name: data.name || ''
        }
        
        let response
        if (editingId) {
          response = await departmentService.update(editingId, submitData)
        } else {
          response = await departmentService.create(submitData)
        }

        if (response.success) {
          toast({
            title: "Success",
            description: `Department ${editingId ? 'updated' : 'created'} successfully`
          })
          form.reset()
          onSuccess?.()
        } else {
          // Handle specific database errors
          let errorMessage = response.error || "Failed to save department"
          if (response.error?.includes('duplicate key value violates unique constraint') && 
              response.error?.includes('departments_code_key')) {
            errorMessage = `Department code "${data.code}" already exists. Please use a different code.`
          } else if (response.error?.includes('duplicate key') && response.error?.includes('code')) {
            errorMessage = `This department code is already in use. Please choose a unique code.`
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

    const response = await departmentService.delete(id)
    
    if (response.success) {
      toast({
        title: "Success",
        description: `Department "${name}" deleted successfully`
      })
      onSuccess?.()
    } else {
      let errorMessage = response.error || "Failed to delete department"
      let errorDetails = ""
      
      // Check for common constraint violation errors
      if (response.error?.includes('foreign key constraint') || 
          response.error?.includes('violates foreign key')) {
        errorMessage = "Cannot delete department - it's still in use"
        errorDetails = "This department has related records (job instances, operators, etc.). Either delete those first or deactivate this department instead."
      } else if (response.error?.includes('dependent')) {
        errorMessage = "Cannot delete department - has dependencies"
        errorDetails = "Other departments or records depend on this one. Consider deactivating instead."
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

    const response = await departmentService.toggleActive(id)
    
    if (response.success) {
      toast({
        title: "Success",
        description: `Department "${name}" ${newStatus ? 'reactivated' : 'deactivated'} successfully`
      })
      onSuccess?.()
    } else {
      toast({
        title: "Error",
        description: response.error || `Failed to ${action} department`,
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