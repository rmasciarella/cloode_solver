import { BaseService, ServiceResponse } from './base.service'
import { Database } from '@/lib/database.types'

type WorkCell = Database['public']['Tables']['work_cells']['Row']
type WorkCellInsert = Database['public']['Tables']['work_cells']['Insert']
type WorkCellUpdate = Database['public']['Tables']['work_cells']['Update']

export class WorkCellService extends BaseService {
  async getAll(activeOnly: boolean = false): Promise<ServiceResponse<WorkCell[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      let query = client
        .from('work_cells')
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

  async getById(id: string): Promise<ServiceResponse<WorkCell>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('work_cells')
        .select('*')
        .eq('cell_id', id)
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async create(workCell: WorkCellInsert): Promise<ServiceResponse<WorkCell>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('work_cells')
        .insert([workCell])
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

  async update(id: string, workCell: WorkCellUpdate): Promise<ServiceResponse<WorkCell>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('work_cells')
        .update(workCell)
        .eq('cell_id', id)
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
        .from('work_cells')
        .delete()
        .eq('cell_id', id)

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(true)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async toggleActive(id: string): Promise<ServiceResponse<WorkCell>> {
    try {
      // First get current status
      const { data: current, error: fetchError } = await (await this.getClient({ fallbackToAnon: true }))
        .from('work_cells')
        .select('is_active')
        .eq('cell_id', id)
        .single()

      if (fetchError) {
        return this.createResponseSync(null, this.handleError(fetchError))
      }

      // Toggle the status
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('work_cells')
        .update({ is_active: !current.is_active })
        .eq('cell_id', id)
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
export const workCellService = new WorkCellService()