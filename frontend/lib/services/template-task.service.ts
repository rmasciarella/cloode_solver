import { BaseService, ServiceResponse } from './base.service'
import { Database } from '@/lib/database.types'

export type TemplateTask = Database['public']['Tables']['template_tasks']['Row']
export type TemplateTaskInsert = Database['public']['Tables']['template_tasks']['Insert']
export type TemplateTaskUpdate = Database['public']['Tables']['template_tasks']['Update']

export interface TemplateTaskWithRelations extends TemplateTask {
  job_templates?: {
    name: string
  }
  departments?: {
    name: string
  }
}

class TemplateTaskService extends BaseService {
  async getAll(): Promise<ServiceResponse<TemplateTaskWithRelations[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('template_tasks')
        .select(`
          *,
          job_templates!inner(name),
          departments(name)
        `)
        .order('position', { ascending: true })

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async getById(id: string): Promise<ServiceResponse<TemplateTaskWithRelations>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('template_tasks')
        .select(`
          *,
          job_templates!inner(name),
          departments(name)
        `)
        .eq('template_task_id', id)
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async create(templateTask: TemplateTaskInsert): Promise<ServiceResponse<TemplateTask>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('template_tasks')
        .insert(templateTask)
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

  async update(id: string, templateTask: TemplateTaskUpdate): Promise<ServiceResponse<TemplateTask>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('template_tasks')
        .update(templateTask)
        .eq('template_task_id', id)
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
        .from('template_tasks')
        .delete()
        .eq('template_task_id', id)

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(true)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async toggleActive(id: string): Promise<ServiceResponse<TemplateTask>> {
    try {
      // First get current status
      const client = await this.getClient({ fallbackToAnon: true })
      const { data: current, error: fetchError } = await client
        .from('template_tasks')
        .select('is_active')
        .eq('template_task_id', id)
        .single()

      if (fetchError) {
        return this.createResponseSync(null, this.handleError(fetchError))
      }

      if (!current) {
        return this.createResponseSync(null, this.handleError(new Error('Template task not found')))
      }

      // Toggle the status
      const { data, error } = await client
        .from('template_tasks')
        .update({ is_active: !current.is_active })
        .eq('template_task_id', id)
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

export const templateTaskService = new TemplateTaskService()