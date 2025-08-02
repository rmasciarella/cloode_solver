import { BaseService, ServiceResponse } from './base.service'
import { Database } from '@/lib/database.types'

type OptimizedPrecedence = Database['public']['Tables']['optimized_precedences']['Row']
type OptimizedPrecedenceInsert = Database['public']['Tables']['optimized_precedences']['Insert']
type OptimizedPrecedenceUpdate = Database['public']['Tables']['optimized_precedences']['Update']

export class OptimizedPrecedenceService extends BaseService {
  async getAll(): Promise<ServiceResponse<OptimizedPrecedence[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_precedences')
        .select('*')
        .order('pattern_id', { ascending: true })

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  // Get precedences by pattern ID
  async getByPatternId(patternId: string): Promise<ServiceResponse<OptimizedPrecedence[]>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_precedences')
        .select('*')
        .eq('pattern_id', patternId)

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data || [])
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async getById(id: string): Promise<ServiceResponse<OptimizedPrecedence>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_precedences')
        .select('*')
        .eq('optimized_precedence_id', id)
        .single()

      if (error) {
        return this.createResponseSync(null, this.handleError(error))
      }

      return this.createResponseSync(data)
    } catch (error) {
      return this.createResponseSync(null, this.handleError(error))
    }
  }

  async create(precedence: OptimizedPrecedenceInsert): Promise<ServiceResponse<OptimizedPrecedence>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_precedences')
        .insert([precedence])
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

  async update(id: string, precedence: OptimizedPrecedenceUpdate): Promise<ServiceResponse<OptimizedPrecedence>> {
    try {
      const client = await this.getClient({ fallbackToAnon: true })
      
      const { data, error } = await client
        .from('optimized_precedences')
        .update(precedence)
        .eq('optimized_precedence_id', id)
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
        .from('optimized_precedences')
        .delete()
        .eq('optimized_precedence_id', id)

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
export const optimizedPrecedenceService = new OptimizedPrecedenceService()