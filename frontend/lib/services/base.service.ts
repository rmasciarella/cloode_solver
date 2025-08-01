import { supabase } from '@/lib/supabase'
import { PostgrestError, SupabaseClient } from '@supabase/supabase-js'
import { Database } from '@/lib/database.types'

// AGENT-3: Fixed ServiceResponse interface to handle exactOptionalPropertyTypes
export interface ServiceResponse<T = any> {
  data: T | null
  error: string | null
  success: boolean
  isAuthenticated?: boolean | undefined
}

export interface ServiceError {
  message: string
  code?: string
  details?: string
  hint?: string
}

export interface ServiceOptions {
  requireAuth?: boolean
  fallbackToAnon?: boolean
}

export abstract class BaseService {
  protected async getClient(_options: ServiceOptions = {}): Promise<SupabaseClient<Database>> {
    // Auth removed - always return the standard client
    return supabase
  }

  protected handleError(error: PostgrestError | Error | any): ServiceError {
    console.error('Service error:', error)
    
    // Handle auth errors gracefully
    if (error.message?.includes('JWT') || error.message?.includes('auth')) {
      return {
        message: 'Authentication error - please try signing in',
        code: error.code || 'AUTH_ERROR'
      }
    }
    
    // Handle Supabase PostgrestError
    if (error.code && error.message) {
      return {
        message: error.message,
        code: error.code,
        details: error.details,
        hint: error.hint
      }
    }
    
    // Handle generic Error
    if (error instanceof Error) {
      return {
        message: error.message
      }
    }
    
    // Handle unknown error
    return {
      message: 'An unexpected error occurred'
    }
  }

  protected async createResponse<T>(
    data: T | null, 
    error: ServiceError | null = null,
    _includeAuthStatus: boolean = false // Default to false for backward compatibility
  ): Promise<ServiceResponse<T>> {
    const response: ServiceResponse<T> = {
      data,
      error: error?.message || null,
      success: error === null
    }

    // Auth removed - never include auth status
    
    return response
  }

  // Legacy synchronous method for backward compatibility
  protected createResponseSync<T>(data: T | null, error: ServiceError | null = null): ServiceResponse<T> {
    return {
      data,
      error: error?.message || null,
      success: error === null
    }
  }

  // AGENT-1: Error response helper for typed error returns
  protected createErrorResponse<T>(error: ServiceError): ServiceResponse<T> {
    return {
      data: null,
      error: error.message,
      success: false
    }
  }

  // Legacy method for backward compatibility
  protected get supabase() {
    return supabase
  }
}