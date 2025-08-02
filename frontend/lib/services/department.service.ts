import { BaseService, ServiceResponse } from './base.service'
import { Database } from '@/lib/database.types'

type Department = Database['public']['Tables']['departments']['Row']
type DepartmentInsert = Database['public']['Tables']['departments']['Insert']
type DepartmentUpdate = Database['public']['Tables']['departments']['Update']

export class DepartmentService extends BaseService {
  async getAll(activeOnly: boolean = false): Promise<ServiceResponse<Department[]>> {
    try {
      // Use auth-aware client with fallback to anonymous access
      const client = await this.getClient({ fallbackToAnon: true })
      
      let query = client
        .from('departments')
        .select('*')
        .order('name', { ascending: true })

      if (activeOnly) {
        query = query.eq('is_active', true)
      }

      const { data, error } = await query

      if (error) {
        return this.createErrorResponse<Department[]>(this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createErrorResponse<Department[]>(this.handleError(error))
    }
  }

  async getById(id: string): Promise<ServiceResponse<Department>> {
    try {
      // Use auth-aware client with fallback to anonymous access
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('departments')
        .select('*')
        .eq('department_id', id)
        .single()

      if (error) {
        return this.createErrorResponse<Department>(this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createErrorResponse<Department>(this.handleError(error))
    }
  }

  async create(department: DepartmentInsert): Promise<ServiceResponse<Department>> {
    try {
      // Use auth-aware client with fallback to anonymous access
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('departments')
        .insert([department])
        .select()
        .single()

      if (error) {
        return this.createErrorResponse<Department>(this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createErrorResponse<Department>(this.handleError(error))
    }
  }

  async update(id: string, department: DepartmentUpdate): Promise<ServiceResponse<Department>> {
    try {
      // Use auth-aware client with fallback to anonymous access
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('departments')
        .update(department)
        .eq('department_id', id)
        .select()
        .single()

      if (error) {
        return this.createErrorResponse<Department>(this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createErrorResponse<Department>(this.handleError(error))
    }
  }

  // AGENT-1: Fixed delete method return type and error responses
  async delete(id: string): Promise<ServiceResponse<boolean>> {
    try {
      // Use auth-aware client with fallback to anonymous access
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { error } = await client
        .from('departments')
        .delete()
        .eq('department_id', id)

      if (error) {
        return this.createErrorResponse<boolean>(this.handleError(error))
      }

      return this.createResponseSync(true)
    } catch (error) {
      return this.createErrorResponse<boolean>(this.handleError(error))
    }
  }

  async toggleActive(id: string): Promise<ServiceResponse<Department>> {
    try {
      // Use auth-aware client with fallback to anonymous access
      const client = await this.getClient({ fallbackToAnon: true })
      
      // First get current status
      const { data: current, error: fetchError } = await client
        .from('departments')
        .select('is_active')
        .eq('department_id', id)
        .single()

      if (fetchError) {
        return this.createErrorResponse<Department>(this.handleError(fetchError))
      }

      // Toggle the status
      const { data, error } = await client
        .from('departments')
        .update({ is_active: !current.is_active })
        .eq('department_id', id)
        .select()
        .single()

      if (error) {
        return this.createErrorResponse<Department>(this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createErrorResponse<Department>(this.handleError(error))
    }
  }
}

// Export singleton instance
export const departmentService = new DepartmentService()