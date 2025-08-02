"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { workCellService } from '@/lib/services'
import { workCellFormSchema, type WorkCellFormData } from '@/lib/schemas'
import { useToast } from '@/hooks/use-toast'

export function useWorkCellForm() {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const form = useForm<WorkCellFormData>({
    resolver: zodResolver(workCellFormSchema),
    defaultValues: {
      name: '',
      capacity: 1,
      department_id: '',
      wip_limit: 5,
      flow_priority: 1,
      floor_location: '',
      cell_type: 'production',
      target_utilization: 85,  // Form input expects percentage (0-100)
      calendar_id: '',
      average_throughput_per_hour: 0,
      is_active: true
    }
  })

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = form

  const onSubmit = async (data: WorkCellFormData, onSuccess?: () => void) => {
    setIsSubmitting(true)
    
    try {
      // Data is already transformed by Zod schema (percentage to decimal)
      const response = await (async () => {
        if (editingId) {
          return await workCellService.update(editingId, data)
        } else {
          // Ensure name is present for create operations
          if (!data.name) {
            throw new Error('Name is required for creating work cells')
          }
          return await workCellService.create(data as WorkCellFormData & { name: string })
        }
      })()

      if (response.success) {
        toast({
          title: "Success",
          description: `Work cell ${editingId ? 'updated' : 'created'} successfully`
        })
        reset()
        setEditingId(null)
        onSuccess?.()
      } else {
        const errorMsg = response.error || "Failed to save work cell"
        
        console.error('Error saving work cell:', response.error)
        toast({
          title: "Error",
          description: errorMsg,
          variant: "destructive"
        })
      }
    } catch (error) {
      const errorMsg = String(error)
      
      toast({
        title: "Error",
        description: "Failed to save work cell",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = (workCell: any) => {
    setEditingId(workCell.cell_id)
    setValue('name', workCell.name)
    setValue('capacity', workCell.capacity)
    setValue('department_id', workCell.department_id || '')
    setValue('wip_limit', workCell.wip_limit || 0)
    setValue('target_utilization', workCell.target_utilization * 100) // Convert decimal to %
    setValue('flow_priority', workCell.flow_priority)
    setValue('floor_location', workCell.floor_location || '')
    setValue('cell_type', workCell.cell_type)
    setValue('is_active', workCell.is_active)
  }

  const handleDelete = async (id: string, onSuccess?: () => void) => {
    if (!confirm('Are you sure you want to delete this work cell?')) return

    const response = await workCellService.delete(id)
    
    if (response.success) {
      toast({
        title: "Success",
        description: "Work cell deleted successfully"
      })
      onSuccess?.()
    } else {
      console.error('Error deleting work cell:', response.error)
      toast({
        title: "Error",
        description: response.error || "Failed to delete work cell",
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
