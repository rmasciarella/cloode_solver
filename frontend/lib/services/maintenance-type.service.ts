import { BaseService, ServiceResponse } from './base.service'
import { Database } from '@/lib/database.types'

type MaintenanceType = Database['public']['Tables']['maintenance_types']['Row']
type MaintenanceTypeInsert = Database['public']['Tables']['maintenance_types']['Insert']
type MaintenanceTypeUpdate = Database['public']['Tables']['maintenance_types']['Update']

export class MaintenanceTypeService extends BaseService {
  async getAll(activeOnly: boolean = false): Promise<ServiceResponse<MaintenanceType[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      let query = client
        .from('maintenance_types')
        .select('*')
        .order('name', { ascending: true })

      if (activeOnly) {
        query = query.eq('is_active', true)
      }

      const { data, error } = await query

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async getById(id: string): Promise<ServiceResponse<MaintenanceType>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('maintenance_types')
        .select('*')
        .eq('maintenance_type_id', id)
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async create(maintenanceType: MaintenanceTypeInsert): Promise<ServiceResponse<MaintenanceType>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('maintenance_types')
        .insert([maintenanceType])
        .select()
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async update(id: string, maintenanceType: MaintenanceTypeUpdate): Promise<ServiceResponse<MaintenanceType>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('maintenance_types')
        .update(maintenanceType)
        .eq('maintenance_type_id', id)
        .select()
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async delete(id: string): Promise<ServiceResponse<boolean>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { error } = await client
        .from('maintenance_types')
        .delete()
        .eq('maintenance_type_id', id)

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(true)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async toggleActive(id: string): Promise<ServiceResponse<MaintenanceType>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      // First get current status
      const { data: current, error: fetchError } = await client
        .from('maintenance_types')
        .select('is_active')
        .eq('maintenance_type_id', id)
        .single()

      if (fetchError) {
        return this.createResponseSync(null, this.handleError(fetchError))
      }

      // Toggle the status
      const { data, error } = await client
        .from('maintenance_types')
        .update({ is_active: !current.is_active })
        .eq('maintenance_type_id', id)
        .select()
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }
}

// Export singleton instance
export const maintenanceTypeService = new MaintenanceTypeService()