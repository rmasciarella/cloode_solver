import { createClient, SupabaseClient } from '@supabase/supabase-js'
import { Database } from './database.types'
import { getSupabaseClient } from './supabase-client'

// Lazy initialization for clients
let _supabase: SupabaseClient<Database> | null = null
let _supabaseServiceRole: SupabaseClient<Database> | null = null

// Default client for frontend operations
export function getSupabaseAuth(): SupabaseClient<Database> {
  if (!_supabase) {
    _supabase = getSupabaseClient()
  }
  return _supabase
}

// Service role client for backend/admin operations (bypass RLS)  
export function getSupabaseServiceRole(): SupabaseClient<Database> {
  if (!_supabaseServiceRole) {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY
    
    if (!supabaseUrl || !supabaseServiceKey) {
      throw new Error('Missing Supabase service role environment variables')
    }
    
    _supabaseServiceRole = createClient<Database>(
      supabaseUrl, 
      supabaseServiceKey,
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false
        }
      }
    )
  }
  return _supabaseServiceRole
}

// For backward compatibility - create proxies that lazily initialize
export const supabase = new Proxy({} as SupabaseClient<Database>, {
  get(target, prop) {
    const client = getSupabaseAuth()
    return client[prop as keyof SupabaseClient<Database>]
  }
})

export const supabaseServiceRole = new Proxy({} as SupabaseClient<Database>, {
  get(target, prop) {
    const client = getSupabaseServiceRole()
    return client[prop as keyof SupabaseClient<Database>]
  }
})

// Development mode flag - set true for development without auth
let _devModeNoAuth: boolean | null = null

export function isDevelopmentNoAuth(): boolean {
  if (_devModeNoAuth === null) {
    _devModeNoAuth = process.env.NODE_ENV === 'development' && 
      process.env.NEXT_PUBLIC_DISABLE_AUTH === 'true'
  }
  return _devModeNoAuth
}

// For backward compatibility - use the function directly
export const DEV_MODE_NO_AUTH = isDevelopmentNoAuth

// Auth helper functions
export const authHelpers = {
  /**
   * Get current user or fallback to service role in dev mode
   */
  async getCurrentUser() {
    if (isDevelopmentNoAuth()) {
      return {
        id: 'dev-user-id',
        email: 'dev@localhost',
        role: 'authenticated'
      }
    }
    
    const { data: { user }, error } = await getSupabaseAuth().auth.getUser()
    return error ? null : user
  },

  /**
   * Get appropriate client based on auth state
   */
  getClient() {
    return isDevelopmentNoAuth() ? getSupabaseServiceRole() : getSupabaseAuth()
  },

  /**
   * Sign in with email/password or continue as anonymous in dev mode
   */
  async signIn(email: string, password: string) {
    if (isDevelopmentNoAuth()) {
      return { data: { user: await this.getCurrentUser() }, error: null }
    }
    
    return await getSupabaseAuth().auth.signInWithPassword({ email, password })
  },

  /**
   * Sign out or no-op in dev mode
   */
  async signOut() {
    if (isDevelopmentNoAuth()) {
      return { error: null }
    }
    
    return await getSupabaseAuth().auth.signOut()
  },

  /**
   * Check if user is authenticated or always true in dev mode
   */
  async isAuthenticated() {
    if (isDevelopmentNoAuth()) return true
    
    const user = await this.getCurrentUser()
    return !!user
  }
}