import { BaseService, ServiceResponse } from './base.service'
import { Database } from '@/lib/database.types'

type OptimizedTask = Database['public']['Tables']['optimized_tasks']['Row']
type OptimizedTaskInsert = Database['public']['Tables']['optimized_tasks']['Insert']
type OptimizedTaskUpdate = Database['public']['Tables']['optimized_tasks']['Update']

export class OptimizedTaskService extends BaseService {
  async getAll(): Promise<ServiceResponse<OptimizedTask[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_tasks')
        .select('*')
        .order('pattern_id', { ascending: true })
        .order('task_sequence', { ascending: true })

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  // Get tasks with pattern details
  async getAllWithPatterns(): Promise<ServiceResponse<any[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_tasks')
        .select(`
          *,
          job_optimized_patterns!optimized_tasks_pattern_id_fkey (
            pattern_id,
            pattern_name
          )
        `)
        .order('pattern_id', { ascending: true })
        .order('task_sequence', { ascending: true })

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  // Get tasks by pattern ID
  async getByPatternId(patternId: string): Promise<ServiceResponse<OptimizedTask[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_tasks')
        .select('*')
        .eq('pattern_id', patternId)
        .order('task_sequence', { ascending: true })

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async getById(id: string): Promise<ServiceResponse<OptimizedTask>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_tasks')
        .select('*')
        .eq('task_id', id)
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async create(task: OptimizedTaskInsert): Promise<ServiceResponse<OptimizedTask>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_tasks')
        .insert([task])
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

  async update(id: string, task: OptimizedTaskUpdate): Promise<ServiceResponse<OptimizedTask>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_tasks')
        .update(task)
        .eq('task_id', id)
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
        .from('optimized_tasks')
        .delete()
        .eq('task_id', id)

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
export const optimizedTaskService = new OptimizedTaskService()