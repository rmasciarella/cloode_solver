"use client"

import { useFormData } from './useFormData'
import { jobTemplateService } from '@/lib/services'
import { Database } from '@/lib/database.types'

type JobTemplate = Database['public']['Tables']['job_optimized_patterns']['Row']

export function useJobTemplateData() {
  const {
    data: jobTemplates,
    loading,
    error,
    refresh: fetchJobTemplates
  } = useFormData<JobTemplate>({
    fetchFn: jobTemplateService.getAll,
    loadOnMount: true
  })

  return {
    jobTemplates,
    loading,
    error,
    fetchJobTemplates
  }
}