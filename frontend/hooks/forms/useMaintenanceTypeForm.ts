import { useState, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { maintenanceTypeService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'
import { usePerformanceMonitor } from '@/lib/performance'
import { maintenanceTypeSchema, type MaintenanceTypeFormData } from '@/lib/schemas/maintenance-type.schema'
import type { MaintenanceType } from './useMaintenanceTypeData'

export function useMaintenanceTypeForm(onSuccess?: () => void) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()
  const performanceMonitor = usePerformanceMonitor('MaintenanceTypeForm')

  const form = useForm<MaintenanceTypeFormData>({
    resolver: zodResolver(maintenanceTypeSchema),
    defaultValues: {
      name: '',
      description: '',
      is_preventive: false,
      is_emergency: false,
      typical_duration_hours: 1,
      blocks_production: false,
      allows_emergency_override: false,
      requires_shutdown: false,
      required_skill_level: '',
      requires_external_vendor: false
    }
  })

  const validateField = useCallback((fieldName: string, value: any) => {
    const startTime = performance.now()
    let isValid = true
    let error = ''

    try {
      switch (fieldName) {
        case 'name':
          isValid = value.length > 0
          error = isValid ? '' : 'Name is required'
          break
        case 'typical_duration_hours':
          isValid = value > 0
          error = isValid ? '' : 'Duration must be positive'
          break
        default:
          isValid = true
      }
    } catch (err) {
      isValid = false
      error = String(err)
    }

    const duration = performance.now() - startTime
    performanceMonitor.track({
      event: 'field_validation',
      duration,
      success: isValid,
      metadata: { field: fieldName, error }
    })
    
    return { isValid, error }
  }, [performanceMonitor])

  const onSubmit = async (data: MaintenanceTypeFormData) => {
    const submitStartTime = Date.now()
    setIsSubmitting(true)
    
    try {
      const formData = {
        name: data.name,
        description: data.description || null,
        is_preventive: data.is_preventive,
        is_emergency: data.is_emergency,
        typical_duration_hours: data.typical_duration_hours,
        blocks_production: data.blocks_production,
        allows_emergency_override: data.allows_emergency_override,
        requires_shutdown: data.requires_shutdown,
        required_skill_level: data.required_skill_level || null,
        requires_external_vendor: data.requires_external_vendor
      }

      let response
      if (editingId) {
        response = await maintenanceTypeService.update(editingId, formData)
      } else {
        response = await maintenanceTypeService.create(formData)
      }

      if (!response.success) {
        throw new Error(response.error || 'Failed to save maintenance type')
      }

      const submitTime = Date.now() - submitStartTime
      performanceMonitor.track({
        event: 'form_submission',
        duration: submitTime,
        success: true,
        metadata: {
          operation: editingId ? 'update' : 'create'
        }
      })

      toast({
        title: "Success",
        description: editingId ? "Maintenance type updated successfully" : "Maintenance type created successfully"
      })

      form.reset()
      setEditingId(null)
      onSuccess?.()
    } catch (error) {
      const submitTime = Date.now() - submitStartTime
      const errorMsg = String(error)
      console.error('Error saving maintenance type:', error)
      
      performanceMonitor.track({
        event: 'form_submission',
        duration: submitTime,
        success: false,
        error: errorMsg,
        metadata: {
          operation: editingId ? 'update' : 'create'
        }
      })
      
      toast({
        title: "Error",
        description: "Failed to save maintenance type",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = useCallback((maintenanceType: MaintenanceType) => {
    performanceMonitor.track({
      event: 'edit_button_click',
      metadata: { maintenance_type_id: maintenanceType.maintenance_type_id }
    })
    
    setEditingId(maintenanceType.maintenance_type_id)
    form.setValue('name', maintenanceType.name)
    form.setValue('description', maintenanceType.description || '')
    form.setValue('is_preventive', maintenanceType.is_preventive)
    form.setValue('is_emergency', maintenanceType.is_emergency)
    form.setValue('typical_duration_hours', maintenanceType.typical_duration_hours)
    form.setValue('blocks_production', maintenanceType.blocks_production)
    form.setValue('allows_emergency_override', maintenanceType.allows_emergency_override)
    form.setValue('requires_shutdown', maintenanceType.requires_shutdown)
    form.setValue('required_skill_level', maintenanceType.required_skill_level || '')
    form.setValue('requires_external_vendor', maintenanceType.requires_external_vendor)
  }, [form, performanceMonitor])

  const handleCancel = useCallback(() => {
    performanceMonitor.track({ event: 'cancel_button_click' })
    form.reset()
    setEditingId(null)
  }, [form, performanceMonitor])

  const handleFieldInteraction = useCallback((event: string, fieldId: string, value?: any) => {
    performanceMonitor.track({
      event: `field_${event}`,
      metadata: { field: fieldId, value }
    })
    
    if (event === 'blur' || event === 'change') {
      validateField(fieldId, value)
    }
  }, [performanceMonitor, validateField])

  return {
    form,
    editingId,
    isSubmitting,
    onSubmit,
    handleEdit,
    handleCancel,
    handleFieldInteraction,
    performanceMonitor
  }
}