"use client"

import { useFormData } from './useFormData'
import { departmentService } from '@/lib/services'
import { Database } from '@/lib/database.types'

type Department = Database['public']['Tables']['departments']['Row']

export function useDepartmentData() {
  const {
    data: departments,
    loading,
    error,
    refresh: fetchDepartments
  } = useFormData<Department>({
    fetchFn: departmentService.getAll,
    loadOnMount: true
  })

  return {
    departments,
    loading,
    error,
    fetchDepartments
  }
}