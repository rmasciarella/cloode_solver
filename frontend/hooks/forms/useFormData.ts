"use client"

import { useState, useEffect, useCallback } from 'react'
import { useToast } from '@/hooks/use-toast'

interface ServiceResponse<T> {
  data: T | null
  error: string | null
  success: boolean
}

interface UseFormDataOptions<T> {
  fetchFn: () => Promise<ServiceResponse<T[]> | T[]>
  onError?: (error: Error) => void
  dependencies?: any[]
  loadOnMount?: boolean
}

export function useFormData<T>({
  fetchFn,
  onError,
  dependencies = [],
  loadOnMount = true
}: UseFormDataOptions<T>) {
  const [data, setData] = useState<T[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const { toast } = useToast()

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await fetchFn()
      
      // Handle both ServiceResponse and direct array returns
      if ('success' in result && 'data' in result) {
        if (result.success && result.data) {
          setData(result.data)
        } else {
          throw new Error(result.error || 'Failed to fetch data')
        }
      } else {
        setData(result as T[])
      }
    } catch (err) {
      const error = err as Error
      setError(error)
      
      if (onError) {
        onError(error)
      } else {
        toast({
          title: "Error",
          description: error.message || "Failed to fetch data",
          variant: "destructive"
        })
      }
    } finally {
      setLoading(false)
    }
  }, [fetchFn, onError, toast])

  useEffect(() => {
    if (loadOnMount) {
      fetchData()
    }
  }, [...dependencies, loadOnMount])

  const refresh = useCallback(() => {
    return fetchData()
  }, [fetchData])

  return {
    data,
    loading,
    error,
    refresh,
    setData
  }
}

// Hook for fetching multiple data sources
export function useMultipleFormData<T extends Record<string, any>>(
  fetchers: { [K in keyof T]: () => Promise<T[K][]> }
) {
  const [data, setData] = useState<{ [K in keyof T]: T[K][] }>({} as any)
  const [loading, setLoading] = useState<{ [K in keyof T]: boolean }>({} as any)
  const [errors, setErrors] = useState<{ [K in keyof T]?: Error }>({})
  const { toast } = useToast()

  useEffect(() => {
    const fetchAll = async () => {
      const loadingState: any = {}
      const errorState: any = {}
      const dataState: any = {}

      // Set all to loading
      Object.keys(fetchers).forEach(key => {
        loadingState[key] = true
      })
      setLoading(loadingState)

      // Fetch all data in parallel
      await Promise.all(
        Object.entries(fetchers).map(async ([key, fetchFn]) => {
          try {
            const result = await (fetchFn as any)()
            dataState[key] = result
            loadingState[key] = false
          } catch (err) {
            const error = err as Error
            errorState[key] = error
            loadingState[key] = false
            
            toast({
              title: `Error loading ${key}`,
              description: error.message || `Failed to fetch ${key}`,
              variant: "destructive"
            })
          }
        })
      )

      setData(dataState)
      setLoading(loadingState)
      setErrors(errorState)
    }

    fetchAll()
  }, [])

  return { data, loading, errors }
}