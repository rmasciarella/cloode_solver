import { BaseService, ServiceResponse } from './base.service'
import { Database } from '@/lib/database.types'

type InstanceTaskAssignment = Database['public']['Tables']['instance_task_assignments']['Row']
type InstanceTaskAssignmentInsert = Database['public']['Tables']['instance_task_assignments']['Insert']
type InstanceTaskAssignmentUpdate = Database['public']['Tables']['instance_task_assignments']['Update']

export class InstanceTaskAssignmentService extends BaseService {
  async getAll(): Promise<ServiceResponse<InstanceTaskAssignment[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('instance_task_assignments')
        .select('*')
        .order('instance_id', { ascending: true })
        .order('task_id', { ascending: true })

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  // Get assignments by instance ID
  async getByInstanceId(instanceId: string): Promise<ServiceResponse<InstanceTaskAssignment[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('instance_task_assignments')
        .select('*')
        .eq('instance_id', instanceId)
        .order('task_id', { ascending: true })

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  // Get assignments by task ID
  async getByTaskId(taskId: string): Promise<ServiceResponse<InstanceTaskAssignment[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('instance_task_assignments')
        .select('*')
        .eq('task_id', taskId)
        .order('instance_id', { ascending: true })

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async getById(id: string): Promise<ServiceResponse<InstanceTaskAssignment>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('instance_task_assignments')
        .select('*')
        .eq('assignment_id', id)
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async create(assignment: InstanceTaskAssignmentInsert): Promise<ServiceResponse<InstanceTaskAssignment>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('instance_task_assignments')
        .insert([assignment])
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

  async update(id: string, assignment: InstanceTaskAssignmentUpdate): Promise<ServiceResponse<InstanceTaskAssignment>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('instance_task_assignments')
        .update(assignment)
        .eq('assignment_id', id)
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
        .from('instance_task_assignments')
        .delete()
        .eq('assignment_id', id)

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
export const instanceTaskAssignmentService = new InstanceTaskAssignmentService()