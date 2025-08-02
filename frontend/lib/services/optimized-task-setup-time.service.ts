import { BaseService, ServiceResponse } from './base.service'
import { Database } from '@/lib/database.types'

type OptimizedTaskSetupTime = Database['public']['Tables']['optimized_task_setup_times']['Row']
type OptimizedTaskSetupTimeInsert = Database['public']['Tables']['optimized_task_setup_times']['Insert']
type OptimizedTaskSetupTimeUpdate = Database['public']['Tables']['optimized_task_setup_times']['Update']

export class OptimizedTaskSetupTimeService extends BaseService {
  async getAll(): Promise<ServiceResponse<OptimizedTaskSetupTime[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_task_setup_times')
        .select('*')
        .order('from_task_id', { ascending: true })
        .order('to_task_id', { ascending: true })

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  // Get setup times by task ID (either from or to)
  async getByTaskId(taskId: string): Promise<ServiceResponse<OptimizedTaskSetupTime[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_task_setup_times')
        .select('*')
        .or(`from_task_id.eq.${taskId},to_task_id.eq.${taskId}`)

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async getById(id: string): Promise<ServiceResponse<OptimizedTaskSetupTime>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_task_setup_times')
        .select('*')
        .eq('setup_id', id)
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async create(setupTime: OptimizedTaskSetupTimeInsert): Promise<ServiceResponse<OptimizedTaskSetupTime>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_task_setup_times')
        .insert([setupTime])
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

  async update(id: string, setupTime: OptimizedTaskSetupTimeUpdate): Promise<ServiceResponse<OptimizedTaskSetupTime>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_task_setup_times')
        .update(setupTime)
        .eq('setup_id', id)
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

  async delete(id: string): Promise<ServiceResponse<void>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { error } = await client
        .from('optimized_task_setup_times')
        .delete()
        .eq('setup_id', id)

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(null)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }
}

// Export singleton instance
export const optimizedTaskSetupTimeService = new OptimizedTaskSetupTimeService()