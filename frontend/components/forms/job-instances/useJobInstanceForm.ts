"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { jobInstanceService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'

export function useJobInstanceForm() {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const form = useForm({
    defaultValues: {
      template_id: '',
      name: '',
      department_id: '',
      priority: 1,
      due_date: '',
      earliest_start_date: new Date().toISOString().split('T')[0],
      customer_order_id: '',
      batch_id: '',
      quantity: 1,
      estimated_cost: 0,
      revenue_value: 0,
      status: 'pending',
      estimated_duration_hours: 0
    }
  })

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = form

  const onSubmit = async (data: any, onSuccess?: () => void) => {
    setIsSubmitting(true)
    
    try {
      const formData = {
        template_id: data.template_id,
        pattern_id: data.template_id,
        name: data.name,
        department_id: data.department_id || null,
        priority: data.priority,
        due_date: data.due_date || null,
        earliest_start_date: data.earliest_start_date,
        customer_order_id: data.customer_order_id || null,
        batch_id: data.batch_id || null,
        quantity: data.quantity,
        estimated_cost: data.estimated_cost || null,
        revenue_value: data.revenue_value || null,
        status: data.status,
        estimated_duration_hours: data.estimated_duration_hours || null
      }

      if (editingId) {
        const response = await jobInstanceService.update(editingId, formData)
        if (!response.success) {
          throw new Error(response.error || 'Failed to update job instance')
        }
        toast({
          title: "Success",
          description: "Job instance updated successfully"
        })
      } else {
        const response = await jobInstanceService.create(formData)
        if (!response.success) {
          throw new Error(response.error || 'Failed to create job instance')
        }
        toast({
          title: "Success",
          description: "Job instance created successfully"
        })
      }

      reset()
      setEditingId(null)
      onSuccess?.()
    } catch (error) {
      console.error('Error saving job instance:', error)
      toast({
        title: "Error",
        description: "Failed to save job instance",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = (instance: any) => {
    setEditingId(instance.instance_id)
    setValue('template_id', instance.template_id)
    setValue('name', instance.name)
    setValue('department_id', instance.department_id || '')
    setValue('priority', instance.priority)
    setValue('due_date', instance.due_date ? instance.due_date.split('T')[0] : '')
    setValue('earliest_start_date', instance.earliest_start_date ? instance.earliest_start_date.split('T')[0] : '')
    setValue('customer_order_id', instance.customer_order_id || '')
    setValue('batch_id', instance.batch_id || '')
    setValue('quantity', instance.quantity)
    setValue('estimated_cost', instance.estimated_cost || 0)
    setValue('revenue_value', instance.revenue_value || 0)
    setValue('status', instance.status)
    setValue('estimated_duration_hours', instance.estimated_duration_hours || 0)
  }

  const handleDelete = async (id: string, onSuccess?: () => void) => {
    if (!confirm('Are you sure you want to delete this job instance?')) return

    try {
      const response = await jobInstanceService.delete(id)
      if (!response.success) {
        throw new Error(response.error || 'Failed to delete job instance')
      }
      toast({
        title: "Success",
        description: "Job instance deleted successfully"
      })
      onSuccess?.()
    } catch (error) {
      console.error('Error deleting job instance:', error)
      toast({
        title: "Error",
        description: "Failed to delete job instance",
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
