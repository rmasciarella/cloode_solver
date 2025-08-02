import { supabase } from '@/lib/supabase'
import { BaseService, ServiceResponse } from './base.service'
import { Database } from '@/lib/database.types'

type BusinessCalendar = Database['public']['Tables']['business_calendars']['Row']
type BusinessCalendarCreate = Database['public']['Tables']['business_calendars']['Insert']
type BusinessCalendarUpdate = Database['public']['Tables']['business_calendars']['Update']

class BusinessCalendarService extends BaseService {
  async getAll(activeOnly: boolean = false): Promise<ServiceResponse<BusinessCalendar[]>> {
    try {
      let query = supabase
        .from('business_calendars')
        .select('*')
        .order('name', { ascending: true })
      
      if (activeOnly) {
        query = query.eq('is_active', true)
      }
      
      const { data, error } = await query
      
      if (error) {
        return this.handleError(error)
      }
      
      return {
        success: true,
        data: data || []
      }
    } catch (error) {
      return this.handleError(error)
    }
  }

  async getById(id: string): Promise<ServiceResponse<BusinessCalendar>> {
    try {
      const { data, error } = await supabase
        .from('business_calendars')
        .select('*')
        .eq('calendar_id', id)
        .single()
      
      if (error) {
        return this.handleError(error)
      }
      
      return {
        success: true,
        data
      }
    } catch (error) {
      return this.handleError(error)
    }
  }

  async create(calendar: BusinessCalendarCreate): Promise<ServiceResponse<BusinessCalendar>> {
    try {
      const { data, error } = await supabase
        .from('business_calendars')
        .insert([calendar])
        .select()
        .single()
      
      if (error) {
        return this.handleError(error)
      }
      
      return {
        success: true,
        data
      }
    } catch (error) {
      return this.handleError(error)
    }
  }

  async update(id: string, calendar: BusinessCalendarUpdate): Promise<ServiceResponse<BusinessCalendar>> {
    try {
      const { data, error } = await supabase
        .from('business_calendars')
        .update(calendar)
        .eq('calendar_id', id)
        .select()
        .single()
      
      if (error) {
        return this.handleError(error)
      }
      
      return {
        success: true,
        data
      }
    } catch (error) {
      return this.handleError(error)
    }
  }

  async delete(id: string): Promise<ServiceResponse<void>> {
    try {
      const { error } = await supabase
        .from('business_calendars')
        .delete()
        .eq('calendar_id', id)
      
      if (error) {
        return this.handleError(error)
      }
      
      return {
        success: true,
        data: undefined
      }
    } catch (error) {
      return this.handleError(error)
    }
  }

  async toggleActive(id: string): Promise<ServiceResponse<BusinessCalendar>> {
    try {
      // First get current status
      const { data: current, error: fetchError } = await supabase
        .from('business_calendars')
        .select('is_active')
        .eq('calendar_id', id)
        .single()
      
      if (fetchError) {
        return this.handleError(fetchError)
      }
      
      // Toggle the status
      const { data, error } = await supabase
        .from('business_calendars')
        .update({ is_active: !current.is_active })
        .eq('calendar_id', id)
        .select()
        .single()
      
      if (error) {
        return this.handleError(error)
      }
      
      return {
        success: true,
        data
      }
    } catch (error) {
      return this.handleError(error)
    }
  }
}

export const businessCalendarService = new BusinessCalendarService()