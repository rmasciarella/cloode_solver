"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { operatorService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'

export function useOperatorForm() {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const form = useForm({
    defaultValues: {
      name: '',
      employee_number: '',
      department_id: '',
      hourly_rate: 25.00,
      max_hours_per_day: 8,
      max_hours_per_week: 40,
      overtime_rate_multiplier: 1.5,
      employment_status: 'active',
      efficiency_rating: 1.00,
      quality_score: 1.00,
      safety_score: 1.00,
      hire_date: '',
      is_active: true
    }
  })

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = form

  const onSubmit = async (data: any, onSuccess?: () => void) => {
    setIsSubmitting(true)
    
    try {
      const formData = {
        name: data.name,
        employee_number: data.employee_number || null,
        department_id: data.department_id || null,
        hourly_rate: data.hourly_rate,
        max_hours_per_day: data.max_hours_per_day,
        max_hours_per_week: data.max_hours_per_week,
        overtime_rate_multiplier: data.overtime_rate_multiplier,
        employment_status: data.employment_status,
        efficiency_rating: data.efficiency_rating,
        quality_score: data.quality_score,
        safety_score: data.safety_score,
        hire_date: data.hire_date || null,
        is_active: data.is_active
      }

      if (editingId) {
        const response = await operatorService.update(editingId, formData)
        if (!response.success) {
          throw new Error(response.error || 'Failed to update operator')
        }
        toast({
          title: "Success",
          description: "Operator updated successfully"
        })
      } else {
        const response = await operatorService.create(formData)
        if (!response.success) {
          throw new Error(response.error || 'Failed to create operator')
        }
        toast({
          title: "Success",
          description: "Operator created successfully"
        })
      }

      reset()
      setEditingId(null)
      onSuccess?.()
    } catch (error) {
      console.error('Error saving operator:', error)
      toast({
        title: "Error",
        description: "Failed to save operator",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = (operator: any) => {
    setEditingId(operator.operator_id)
    setValue('name', operator.name)
    setValue('employee_number', operator.employee_number || '')
    setValue('department_id', operator.department_id || '')
    setValue('hourly_rate', operator.hourly_rate)
    setValue('max_hours_per_day', operator.max_hours_per_day)
    setValue('max_hours_per_week', operator.max_hours_per_week)
    setValue('overtime_rate_multiplier', operator.overtime_rate_multiplier)
    setValue('employment_status', operator.employment_status)
    setValue('efficiency_rating', operator.efficiency_rating)
    setValue('quality_score', operator.quality_score)
    setValue('safety_score', operator.safety_score)
    setValue('is_active', operator.is_active)
  }

  const handleDelete = async (id: string, onSuccess?: () => void) => {
    if (!confirm('Are you sure you want to delete this operator?')) return

    try {
      const response = await operatorService.delete(id)
      if (!response.success) {
        throw new Error(response.error || 'Failed to delete operator')
      }
      toast({
        title: "Success",
        description: "Operator deleted successfully"
      })
      onSuccess?.()
    } catch (error) {
      console.error('Error deleting operator:', error)
      toast({
        title: "Error",
        description: "Failed to delete operator",
        variant: "destructive"
      })
    }
  }

  const handleCancel = () => {
    reset()
    setEditingId(null)
  }

  return {
    form,
    register,
    handleSubmit: (onSuccess?: () => void) => handleSubmit((data) => onSubmit(data, onSuccess)),
    reset,
    setValue,
    watch,
    errors,
    editingId,
    isSubmitting,
    handleEdit,
    handleDelete,
    handleCancel
  }
}
