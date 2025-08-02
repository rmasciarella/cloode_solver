"use client"

import { useState, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { optimizedPrecedenceService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'

type TemplatePrecedence = {
  precedence_id: string
  pattern_id: string
  predecessor_task_id: string
  successor_task_id: string
  created_at: string
  // These fields may not exist in the database yet
  min_delay_minutes?: number
  max_delay_minutes?: number | null
  requires_department_transfer?: boolean
  transfer_time_minutes?: number
}

type TemplatePrecedenceFormData = {
  pattern_id: string
  predecessor_optimized_task_id: string
  successor_optimized_task_id: string
  min_delay_minutes: number
  max_delay_minutes: number
  requires_department_transfer: boolean
  transfer_time_minutes: number
}

export function useTemplatePrecedenceForm(fetchTemplatePrecedences: () => void) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<TemplatePrecedenceFormData>({
    defaultValues: {
      pattern_id: '',
      predecessor_optimized_task_id: '',
      successor_optimized_task_id: '',
      min_delay_minutes: 0,
      max_delay_minutes: 0,
      requires_department_transfer: false,
      transfer_time_minutes: 0
    }
  })

  const onSubmit = async (data: TemplatePrecedenceFormData) => {
    setIsSubmitting(true)
    try {
      if (data.predecessor_optimized_task_id === data.successor_optimized_task_id) {
        toast({
          title: "Error",
          description: "Predecessor and successor tasks must be different",
          variant: "destructive"
        })
        setIsSubmitting(false)
        return
      }

      const formData = {
        pattern_id: data.pattern_id,
        predecessor_task_id: data.predecessor_optimized_task_id,  // Map to correct field name
        successor_task_id: data.successor_optimized_task_id,      // Map to correct field name
        // These fields may not exist in the database yet, so we'll omit them
        // min_delay_minutes: data.min_delay_minutes,
        // max_delay_minutes: data.max_delay_minutes || null,
        // requires_department_transfer: data.requires_department_transfer,
        // transfer_time_minutes: data.transfer_time_minutes
      }

      if (editingId) {
        const response = await optimizedPrecedenceService.update(editingId, formData)

        if (!response.success) {
          throw new Error(response.error || 'Failed to update template precedence')
        }

        toast({
          title: "Success",
          description: "Template precedence updated successfully"
        })
      } else {
        const response = await optimizedPrecedenceService.create(formData)

        if (!response.success) {
          throw new Error(response.error || 'Failed to create template precedence')
        }

        toast({
          title: "Success",
          description: "Template precedence created successfully"
        })
      }

      reset()
      setEditingId(null)
      fetchTemplatePrecedences()
    } catch (error) {
      console.error('Error saving template precedence:', error)
      toast({
        title: "Error",
        description: "Failed to save template precedence",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = useCallback((precedence: TemplatePrecedence) => {
    setEditingId(precedence.precedence_id)
    setValue('pattern_id', precedence.pattern_id)
    setValue('predecessor_optimized_task_id', precedence.predecessor_task_id)
    setValue('successor_optimized_task_id', precedence.successor_task_id)
    setValue('min_delay_minutes', precedence.min_delay_minutes || 0)
    setValue('max_delay_minutes', precedence.max_delay_minutes || 0)
    setValue('requires_department_transfer', precedence.requires_department_transfer || false)
    setValue('transfer_time_minutes', precedence.transfer_time_minutes || 0)
  }, [setValue])

  const handleDelete = useCallback(async (id: string) => {
    if (!confirm('Are you sure you want to delete this template precedence?')) return

    try {
      const response = await optimizedPrecedenceService.delete(id)

      if (!response.success) {
        throw new Error(response.error || 'Failed to delete template precedence')
      }

      toast({
        title: "Success",
        description: "Template precedence deleted successfully"
      })
      fetchTemplatePrecedences()
    } catch (error) {
      console.error('Error deleting template precedence:', error)
      toast({
        title: "Error",
        description: "Failed to delete template precedence",
        variant: "destructive"
      })
    }
  }, [toast, fetchTemplatePrecedences])

  const handleCancel = useCallback(() => {
    reset()
    setEditingId(null)
  }, [reset])

  return {
    register,
    handleSubmit,
    setValue,
    watch,
    errors,
    editingId,
    isSubmitting,
    onSubmit,
    handleEdit,
    handleDelete,
    handleCancel
  }
}
