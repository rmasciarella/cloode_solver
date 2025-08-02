import { useState, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { optimizedTaskSetupTimeService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'
import { usePerformanceMonitor, performanceUtils } from '@/hooks/use-performance-monitor'
import { setupTimeSchema, type SetupTimeFormData } from '@/lib/schemas/setup-time.schema'
import type { SetupTime } from './useSetupTimeData'

export function useSetupTimeForm(onSuccess?: () => void) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()
  const monitor = usePerformanceMonitor('SetupTimeForm')

  const form = useForm<SetupTimeFormData>({
    resolver: zodResolver(setupTimeSchema),
    defaultValues: {
      from_optimized_task_id: '',
      to_optimized_task_id: '',
      machine_resource_id: '',
      setup_time_minutes: 15,
      setup_type: 'standard',
      complexity_level: 'simple',
      requires_operator_skill: '',
      requires_certification: false,
      requires_supervisor_approval: false,
      setup_cost: 0,
      efficiency_impact_percent: 0,
      product_family_from: '',
      product_family_to: ''
    }
  })

  const validateField = useCallback((fieldName: string, value: any) => {
    const startTime = performance.now()
    let isValid = true
    let error = ''

    try {
      switch (fieldName) {
        case 'setup_time_minutes':
          isValid = value >= 0
          error = isValid ? '' : 'Setup time must be non-negative'
          break
        case 'setup_cost':
          isValid = value >= 0
          error = isValid ? '' : 'Cost must be non-negative'
          break
        case 'efficiency_impact_percent':
          isValid = value >= 0 && value <= 100
          error = isValid ? '' : 'Impact must be between 0 and 100%'
          break
        default:
          isValid = true
      }
    } catch (err) {
      isValid = false
      error = String(err)
    }

    const duration = performance.now() - startTime
    monitor.recordValidation(fieldName, duration, isValid, error)
    
    return { isValid, error }
  }, [monitor])

  const onSubmit = async (data: SetupTimeFormData) => {
    setIsSubmitting(true)
    monitor.startTimer('form_submission')
    
    try {
      if (data.from_optimized_task_id === data.to_optimized_task_id) {
        monitor.endTimer('form_submission', 'form_submission_validation_error', false, 'From and To tasks must be different')
        
        toast({
          title: "Error",
          description: "From and To tasks must be different",
          variant: "destructive"
        })
        setIsSubmitting(false)
        return
      }

      const formData = {
        from_optimized_task_id: data.from_optimized_task_id,
        to_optimized_task_id: data.to_optimized_task_id,
        machine_resource_id: data.machine_resource_id,
        setup_time_minutes: data.setup_time_minutes,
        setup_type: data.setup_type,
        complexity_level: data.complexity_level,
        requires_operator_skill: data.requires_operator_skill || null,
        requires_certification: data.requires_certification,
        requires_supervisor_approval: data.requires_supervisor_approval,
        setup_cost: data.setup_cost,
        efficiency_impact_percent: data.efficiency_impact_percent,
        product_family_from: data.product_family_from || null,
        product_family_to: data.product_family_to || null,
      }

      const { duration } = await performanceUtils.measureAsync(
        async () => {
          if (editingId) {
            const response = await optimizedTaskSetupTimeService.update(editingId, formData)
            if (!response.success) {
              throw new Error(response.error || 'Failed to update setup time')
            }
            return 'update'
          } else {
            const response = await optimizedTaskSetupTimeService.create(formData)
            if (!response.success) {
              throw new Error(response.error || 'Failed to create setup time')
            }
            return 'insert'
          }
        },
        'SetupTimeForm',
        editingId ? 'supabase_update_setup_time' : 'supabase_insert_setup_time',
        { 
          editing: !!editingId,
          setup_time_minutes: data.setup_time_minutes,
          setup_type: data.setup_type,
          complexity_level: data.complexity_level
        }
      )

      const totalDuration = monitor.endTimer('form_submission', 'form_submission_success', true)
      monitor.recordSubmission(totalDuration, true, undefined, {
        operation: editingId ? 'update' : 'create',
        database_duration: duration,
        total_duration: totalDuration
      })

      toast({
        title: "Success",
        description: editingId ? "Setup time updated successfully" : "Setup time created successfully"
      })

      form.reset()
      setEditingId(null)
      onSuccess?.()
    } catch (error) {
      const errorMsg = String(error)
      console.error('Error saving setup time:', error)
      
      const totalDuration = monitor.endTimer('form_submission', 'form_submission_error', false, errorMsg)
      monitor.recordSubmission(totalDuration, false, errorMsg, {
        operation: editingId ? 'update' : 'create'
      })
      
      toast({
        title: "Error",
        description: "Failed to save setup time",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = useCallback((setupTime: SetupTime) => {
    monitor.recordInteraction('edit_button_click', undefined, { setup_time_id: setupTime.setup_time_id })
    
    monitor.startTimer('populate_form')
    setEditingId(setupTime.setup_time_id)
    form.setValue('from_optimized_task_id', setupTime.from_optimized_task_id)
    form.setValue('to_optimized_task_id', setupTime.to_optimized_task_id)
    form.setValue('machine_resource_id', setupTime.machine_resource_id)
    form.setValue('setup_time_minutes', setupTime.setup_time_minutes)
    form.setValue('setup_type', setupTime.setup_type)
    form.setValue('complexity_level', setupTime.complexity_level)
    form.setValue('requires_operator_skill', setupTime.requires_operator_skill || '')
    form.setValue('requires_certification', setupTime.requires_certification)
    form.setValue('requires_supervisor_approval', setupTime.requires_supervisor_approval)
    form.setValue('setup_cost', setupTime.setup_cost)
    form.setValue('efficiency_impact_percent', setupTime.efficiency_impact_percent)
    monitor.endTimer('populate_form', 'populate_form_for_edit', true)
  }, [form, monitor])

  const handleCancel = useCallback(() => {
    monitor.recordInteraction('cancel_button_click')
    form.reset()
    setEditingId(null)
  }, [form, monitor])

  const handleFieldFocus = useCallback((fieldId: string) => {
    monitor.recordInteraction('focus', fieldId)
  }, [monitor])

  const handleFieldBlur = useCallback((fieldId: string, value: any) => {
    monitor.recordInteraction('blur', fieldId)
    validateField(fieldId, value)
  }, [monitor, validateField])

  const handleFieldChange = useCallback((fieldId: string, value: any) => {
    monitor.recordInteraction('change', fieldId, { value: typeof value === 'string' ? value.length : value })
    validateField(fieldId, value)
  }, [monitor, validateField])

  return {
    form,
    editingId,
    isSubmitting,
    onSubmit,
    handleEdit,
    handleCancel,
    handleFieldFocus,
    handleFieldBlur,
    handleFieldChange,
    monitor
  }
}