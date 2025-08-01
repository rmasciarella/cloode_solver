import { getSupabaseClient } from './supabase-client'
import { SupabaseClient } from '@supabase/supabase-js'
import { Database } from './database.types'

// Re-export the supabase client with lazy initialization using proxy pattern
// This prevents module-level initialization that causes serverless failures
export const supabase = new Proxy({} as SupabaseClient<Database>, {
  get(target, prop) {
    const client = getSupabaseClient()
    return client[prop as keyof SupabaseClient<Database>]
  }
})