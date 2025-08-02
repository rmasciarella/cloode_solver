"use client"

import { useState, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { optimizedTaskService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'
import { useFormPerformance } from '@/lib/hooks/use-form-performance'

type OptimizedTask = {
  optimized_task_id: string
  pattern_id: string
  name: string
  position: number
  department_id: string | null
  is_unattended: boolean
  is_setup: boolean
  sequence_id: string | null
  min_operators: number
  max_operators: number
  operator_efficiency_curve: string | null
  created_at: string
}

type OptimizedTaskFormData = {
  pattern_id: string
  name: string
  position: number
  department_id: string
  is_unattended: boolean
  is_setup: boolean
  sequence_id: string
  min_operators: number
  max_operators: number
  operator_efficiency_curve: string
}

export function useTemplateTaskForm(fetchOptimizedTasks: () => void) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()
  
  // Performance monitoring
  const performanceTracker = useFormPerformance('template-task-form')

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<OptimizedTaskFormData>({
    defaultValues: {
      pattern_id: '',
      name: '',
      position: 1,
      department_id: '',
      is_unattended: false,
      is_setup: false,
      sequence_id: '',
      min_operators: 1,
      max_operators: 1,
      operator_efficiency_curve: 'linear'
    }
  })

  const onSubmit = async (data: OptimizedTaskFormData) => {
    setIsSubmitting(true)
    performanceTracker.trackSubmissionStart()
    
    try {
      const formData = {
        pattern_id: data.pattern_id,
        name: data.name,
        position: data.position,
        department_id: data.department_id || null,
        is_unattended: data.is_unattended,
        is_setup: data.is_setup,
        sequence_id: data.sequence_id || null,
        min_operators: data.min_operators,
        max_operators: data.max_operators,
        operator_efficiency_curve: data.operator_efficiency_curve || null
      }

      if (editingId) {
        const response = await optimizedTaskService.update(editingId, formData)

        if (!response.success) {
          throw new Error(response.error || 'Failed to update optimized task')
        }

        toast({
          title: "Success",
          description: "Optimized task updated successfully"
        })
      } else {
        const response = await optimizedTaskService.create(formData)

        if (!response.success) {
          throw new Error(response.error || 'Failed to create optimized task')
        }

        toast({
          title: "Success",
          description: "Optimized task created successfully"
        })
      }

      reset()
      setEditingId(null)
      fetchOptimizedTasks()
      performanceTracker.trackSubmissionEnd(true)
    } catch (error) {
      console.error('Error saving optimized task:', error)
      performanceTracker.trackSubmissionEnd(false)
      toast({
        title: "Error",
        description: "Failed to save optimized task",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = useCallback((task: OptimizedTask) => {
    setEditingId(task.optimized_task_id)
    setValue('pattern_id', task.pattern_id)
    setValue('name', task.name)
    setValue('position', task.position)
    setValue('department_id', task.department_id || '')
    setValue('is_unattended', task.is_unattended)
    setValue('is_setup', task.is_setup)
    setValue('sequence_id', task.sequence_id || '')
    setValue('operator_efficiency_curve', task.operator_efficiency_curve || 'linear')
    setValue('min_operators', task.min_operators)
    setValue('max_operators', task.max_operators)
  }, [setValue])

  const handleDelete = useCallback(async (id: string) => {
    if (!confirm('Are you sure you want to delete this optimized task?')) return

    try {
      const response = await optimizedTaskService.delete(id)

      if (!response.success) {
        throw new Error(response.error || 'Failed to delete optimized task')
      }

      toast({
        title: "Success",
        description: "Optimized task deleted successfully"
      })
      fetchOptimizedTasks()
    } catch (error) {
      console.error('Error deleting optimized task:', error)
      toast({
        title: "Error",
        description: "Failed to delete optimized task",
        variant: "destructive"
      })
    }
  }, [toast, fetchOptimizedTasks])

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
    handleCancel,
    performanceTracker
  }
}
