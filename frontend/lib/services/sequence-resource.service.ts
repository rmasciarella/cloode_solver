import { BaseService, ServiceResponse } from './base.service'
import { Database } from '@/lib/database.types'

type SequenceResource = Database['public']['Tables']['sequence_resources']['Row']
type SequenceResourceInsert = Database['public']['Tables']['sequence_resources']['Insert']
type SequenceResourceUpdate = Database['public']['Tables']['sequence_resources']['Update']

export class SequenceResourceService extends BaseService {
  async getAll(activeOnly: boolean = false): Promise<ServiceResponse<SequenceResource[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      let query = client
        .from('sequence_resources')
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

  async getById(id: string): Promise<ServiceResponse<SequenceResource>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('sequence_resources')
        .select('*')
        .eq('resource_id', id)
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  // Get sequence resources with just ID and name (for dropdowns)
  async getSequenceOptions(): Promise<ServiceResponse<Array<{ sequence_id: number, name: string }>>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('sequence_resources')
        .select('sequence_id, name')
        .order('sequence_id', { ascending: true })

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async create(sequenceResource: SequenceResourceInsert): Promise<ServiceResponse<SequenceResource>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('sequence_resources')
        .insert([sequenceResource])
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

  async update(id: string, sequenceResource: SequenceResourceUpdate): Promise<ServiceResponse<SequenceResource>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('sequence_resources')
        .update(sequenceResource)
        .eq('resource_id', id)
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
        .from('sequence_resources')
        .delete()
        .eq('resource_id', id)

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(true)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async toggleActive(id: string): Promise<ServiceResponse<SequenceResource>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      // First get current status
      const { data: current, error: fetchError } = await client
        .from('sequence_resources')
        .select('is_active')
        .eq('resource_id', id)
        .single()

      if (fetchError) {
        return this.createResponseSync(null, this.handleError(fetchError))
      }

      // Toggle the status
      const { data, error } = await client
        .from('sequence_resources')
        .update({ is_active: !current.is_active })
        .eq('resource_id', id)
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
export const sequenceResourceService = new SequenceResourceService()