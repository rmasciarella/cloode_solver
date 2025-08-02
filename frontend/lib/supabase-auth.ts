import { SupabaseClient } from '@supabase/supabase-js'
import { Database } from './database.types'
import { getSupabaseClient } from './supabase-client'

// Lazy initialization - client is created on first access
let _supabase: SupabaseClient<Database> | null = null

export function getSupabase(): SupabaseClient<Database> {
  if (!_supabase) {
    _supabase = getSupabaseClient()
  }
  return _supabase
}

// For backward compatibility - create a getter that lazily initializes
export const supabase = new Proxy({} as SupabaseClient<Database>, {
  get(_target, prop) {
    const client = getSupabase()
    return client[prop as keyof SupabaseClient<Database>]
  }
})

// Auth-aware client wrapper that automatically handles token context
export class AuthAwareSupabaseClient {
  private client: SupabaseClient<Database> | null = null

  constructor() {
    // Don't initialize client in constructor
  }

  // Lazy initialization of client
  private getClient(): SupabaseClient<Database> {
    if (!this.client) {
      this.client = getSupabaseClient()
    }
    return this.client
  }

  // Get client with current auth context
  getClientInstance(): SupabaseClient<Database> {
    return this.getClient()
  }

  // Get client explicitly for authenticated requests
  getAuthenticatedClient(): SupabaseClient<Database> {
    return this.getClient()
  }

  // Get client explicitly for anonymous requests (fallback mode)
  getAnonymousClient(): SupabaseClient<Database> {
    return this.getClient()
  }

  // Check if user is authenticated
  async isAuthenticated(): Promise<boolean> {
    const { data: { session } } = await this.getClient().auth.getSession()
    return !!session
  }

  // Get current user
  async getCurrentUser() {
    const { data: { user } } = await this.getClient().auth.getUser()
    return user
  }

  // Enhanced query with auth fallback
  async query<T>(
    table: string,
    operation: 'select' | 'insert' | 'update' | 'delete' = 'select',
    options: {
      requireAuth?: boolean
      fallbackToAnon?: boolean
      columns?: string
      filters?: Record<string, any>
      data?: any
    } = {}
  ) {
    const {
      requireAuth = false,
      fallbackToAnon = true,
      columns = '*',
      filters = {},
      data
    } = options

    const isAuth = await this.isAuthenticated()

    // Check auth requirements
    if (requireAuth && !isAuth && !fallbackToAnon) {
      throw new Error('Authentication required for this operation')
    }

    // Build query
    let query: any = this.getClient().from(table)

    switch (operation) {
      case 'select':
        query = query.select(columns)
        break
      case 'insert':
        query = query.insert(data)
        break
      case 'update':
        query = query.update(data)
        break
      case 'delete':
        query = query.delete()
        break
    }

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      query = query.eq(key, value)
    })

    return query
  }
}

// Export singleton instance for use throughout the app
export const authAwareSupabase = new AuthAwareSupabaseClient()

// Note: Original supabase client is already exported from @/lib/supabase
// We don't re-export it here to avoid conflicts