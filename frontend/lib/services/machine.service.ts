import { BaseService, ServiceResponse } from './base.service'
import { Database } from '@/lib/database.types'

type Machine = Database['public']['Tables']['machines']['Row']
type MachineInsert = Database['public']['Tables']['machines']['Insert']
type MachineUpdate = Database['public']['Tables']['machines']['Update']

export class MachineService extends BaseService {
  async getAll(activeOnly: boolean = false): Promise<ServiceResponse<Machine[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      let query = client
        .from('machines')
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

  async getById(id: string): Promise<ServiceResponse<Machine>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('machines')
        .select('*')
        .eq('machine_resource_id', id)
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async create(machine: MachineInsert): Promise<ServiceResponse<Machine>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('machines')
        .insert([machine])
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

  async update(id: string, machine: MachineUpdate): Promise<ServiceResponse<Machine>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('machines')
        .update(machine)
        .eq('machine_resource_id', id)
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

  // AGENT-3: Fixed delete method return type
  async delete(id: string): Promise<ServiceResponse<boolean>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { error } = await client
        .from('machines')
        .delete()
        .eq('machine_resource_id', id)

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(true)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async toggleActive(id: string): Promise<ServiceResponse<Machine>> {
    try {
      // First get current status
      const client = await this.getClient({ fallbackToAnon: true })
      const { data: current, error: fetchError } = await client
        .from('machines')
        .select('is_active')
        .eq('machine_resource_id', id)
        .single()

      if (fetchError) {
        return this.createResponseSync(null, this.handleError(fetchError))
      }

      // Toggle the status
      const { data, error } = await client
        .from('machines')
        .update({ is_active: !current.is_active })
        .eq('machine_resource_id', id)
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
export const machineService = new MachineService()