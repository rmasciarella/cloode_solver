import { BaseService, ServiceResponse } from './base.service'
import { Database } from '@/lib/database.types'

type JobInstance = Database['public']['Tables']['job_instances']['Row']
type JobInstanceInsert = Database['public']['Tables']['job_instances']['Insert']
type JobInstanceUpdate = Database['public']['Tables']['job_instances']['Update']

export class JobInstanceService extends BaseService {
  async getAll(activeOnly: boolean = false): Promise<ServiceResponse<JobInstance[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      let query = client
        .from('job_instances')
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

  // Get all with job pattern details
  async getAllWithPatterns(): Promise<ServiceResponse<any[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('job_instances')
        .select(`
          *,
          job_optimized_patterns!job_instances_template_id_fkey (
            pattern_id,
            pattern_name
          )
        `)
        .order('name', { ascending: true })

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async getById(id: string): Promise<ServiceResponse<JobInstance>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('job_instances')
        .select('*')
        .eq('instance_id', id)
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async create(jobInstance: JobInstanceInsert): Promise<ServiceResponse<JobInstance>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('job_instances')
        .insert([jobInstance])
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

  async update(id: string, jobInstance: JobInstanceUpdate): Promise<ServiceResponse<JobInstance>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('job_instances')
        .update(jobInstance)
        .eq('instance_id', id)
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
        .from('job_instances')
        .delete()
        .eq('instance_id', id)

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(true)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async toggleActive(id: string): Promise<ServiceResponse<JobInstance>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      // First get current status
      const { data: current, error: fetchError } = await client
        .from('job_instances')
        .select('is_active')
        .eq('instance_id', id)
        .single()

      if (fetchError) {
        return this.createResponseSync(null, this.handleError(fetchError))
      }

      // Toggle the status
      const { data, error } = await client
        .from('job_instances')
        .update({ is_active: !current.is_active })
        .eq('instance_id', id)
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
export const jobInstanceService = new JobInstanceService()