"use client"

import { useState, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { machineFormSchema, type MachineFormData } from '@/lib/schemas'
import { machineService } from '@/lib/services'
import { Database } from '@/lib/database.types'
import { useToast } from '@/hooks/use-toast'
import { useOptimizedPerformance } from '@/hooks/useOptimizedPerformance'

type Machine = Database['public']['Tables']['machines']['Row']

interface UseMachineFormReturn {
  form: ReturnType<typeof useForm<MachineFormData>>
  editingId: string | null
  isSubmitting: boolean
  startEdit: (machine: Machine) => void
  cancelEdit: () => void
  onSubmit: (data: MachineFormData) => Promise<void>
  onDelete: (id: string) => Promise<void>
}

export function useMachineForm(
  onMachineUpdated?: () => void
): UseMachineFormReturn {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()
  const performanceTracker = useOptimizedPerformance('machine-form-operations')

  const form = useForm<MachineFormData>({
    resolver: zodResolver(machineFormSchema),
    defaultValues: {
      machine_resource_id: '',
      machine_name: '',
      department_id: '',
      work_cell_id: '',
      description: '',
      capacity: 1,
      efficiency: 100,
      availability: 100,
      status: 'active',
      hourly_rate: 0,
      setup_time_minutes: 0,
      maintenance_required: false,
      shift_pattern: 'standard',
      max_concurrent_jobs: 1
    }
  })

  const startEdit = useCallback((machine: Machine) => {
    setEditingId(machine.machine_resource_id)
    
    // Map database fields to form fields
    form.reset({
      machine_resource_id: machine.machine_resource_id,
      machine_name: machine.machine_name,
      department_id: machine.department_id || '',
      work_cell_id: machine.work_cell_id || '',
      description: machine.description || '',
      capacity: machine.capacity || 1,
      efficiency: machine.efficiency || 100,
      availability: machine.availability || 100,
      status: machine.status || 'active',
      hourly_rate: machine.hourly_rate || 0,
      setup_time_minutes: machine.setup_time_minutes || 0,
      maintenance_required: machine.maintenance_required || false,
      shift_pattern: machine.shift_pattern || 'standard',
      max_concurrent_jobs: machine.max_concurrent_jobs || 1
    })
  }, [form])

  const cancelEdit = useCallback(() => {
    setEditingId(null)
    form.reset()
  }, [form])

  const onSubmit = useCallback(async (data: MachineFormData) => {
    const endTiming = performanceTracker.startTiming('form-submit')
    performanceTracker.trackInteraction('form-submit', { editingId })
    
    try {
      setIsSubmitting(true)

      let response
      if (editingId) {
        response = await machineService.update(editingId, data)
      } else {
        response = await machineService.create(data)
      }

      if (response.error) {
        throw new Error(response.error.message)
      }

      toast({
        title: "Success",
        description: `Machine ${editingId ? 'updated' : 'created'} successfully`,
      })

      performanceTracker.trackFormSubmit(true, { operation: editingId ? 'update' : 'create' })
      
      // Reset form and editing state
      form.reset()
      setEditingId(null)
      
      // Trigger data refresh
      onMachineUpdated?.()

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Operation failed'
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      })

      performanceTracker.trackFormSubmit(false, { error: errorMessage })
      performanceTracker.trackError(
        error instanceof Error ? error : new Error(errorMessage), 
        'form-submit'
      )
    } finally {
      setIsSubmitting(false)
      endTiming()
    }
  }, [editingId, form, toast, performanceTracker, onMachineUpdated])

  const onDelete = useCallback(async (id: string) => {
    const endTiming = performanceTracker.startTiming('delete-operation')
    
    try {
      const response = await machineService.delete(id)

      if (response.error) {
        throw new Error(response.error.message)
      }

      toast({
        title: "Success",
        description: "Machine deleted successfully",
      })

      // Trigger data refresh
      onMachineUpdated?.()

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Delete failed'
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      })

      performanceTracker.trackError(
        error instanceof Error ? error : new Error(errorMessage), 
        'delete-operation'
      )
    } finally {
      endTiming()
    }
  }, [toast, performanceTracker, onMachineUpdated])

  return {
    form,
    editingId,
    isSubmitting,
    startEdit,
    cancelEdit,
    onSubmit,
    onDelete
  }
}