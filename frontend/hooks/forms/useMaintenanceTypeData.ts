import { useState, useEffect, useCallback } from 'react'
import { maintenanceTypeService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'
import { usePerformanceMonitor } from '@/lib/performance'

export type MaintenanceType = {
  maintenance_type_id: string
  name: string
  description: string | null
  is_preventive: boolean
  is_emergency: boolean
  typical_duration_hours: number
  blocks_production: boolean
  allows_emergency_override: boolean
  requires_shutdown: boolean
  required_skill_level: string | null
  requires_external_vendor: boolean
  created_at: string
}

export function useMaintenanceTypeData() {
  const [maintenanceTypes, setMaintenanceTypes] = useState<MaintenanceType[]>([])
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()
  const performanceMonitor = usePerformanceMonitor('MaintenanceTypeForm')

  const fetchMaintenanceTypes = useCallback(async () => {
    const fetchStartTime = Date.now()
    setLoading(true)
    
    try {
      const response = await maintenanceTypeService.getAll()
      
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch maintenance types')
      }
      
      const fetchTime = Date.now() - fetchStartTime
      performanceMonitor.track({
        event: 'fetch_maintenance_types',
        duration: fetchTime,
        success: true,
        metadata: {
          recordCount: response.data?.length || 0
        }
      })
      
      setMaintenanceTypes(response.data || [])
    } catch (error) {
      const fetchTime = Date.now() - fetchStartTime
      console.error('Error fetching maintenance types:', error)
      
      performanceMonitor.track({
        event: 'fetch_maintenance_types',
        duration: fetchTime,
        success: false,
        error: String(error)
      })
      
      toast({
        title: "Error",
        description: "Failed to fetch maintenance types",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }, [toast, performanceMonitor])

  const deleteMaintenanceType = useCallback(async (id: string) => {
    const deleteStartTime = Date.now()
    
    try {
      const response = await maintenanceTypeService.delete(id)
      
      if (!response.success) {
        throw new Error(response.error || 'Failed to delete maintenance type')
      }

      const deleteTime = Date.now() - deleteStartTime
      performanceMonitor.track({
        event: 'delete_maintenance_type',
        duration: deleteTime,
        success: true,
        metadata: { maintenance_type_id: id }
      })

      toast({
        title: "Success",
        description: "Maintenance type deleted successfully"
      })
      
      await fetchMaintenanceTypes()
    } catch (error) {
      const deleteTime = Date.now() - deleteStartTime
      console.error('Error deleting maintenance type:', error)
      
      performanceMonitor.track({
        event: 'delete_maintenance_type',
        duration: deleteTime,
        success: false,
        error: String(error)
      })
      
      toast({
        title: "Error",
        description: "Failed to delete maintenance type",
        variant: "destructive"
      })
      throw error
    }
  }, [toast, fetchMaintenanceTypes, performanceMonitor])

  useEffect(() => {
    fetchMaintenanceTypes()
  }, [fetchMaintenanceTypes])

  return {
    maintenanceTypes,
    loading,
    fetchMaintenanceTypes,
    deleteMaintenanceType
  }
}