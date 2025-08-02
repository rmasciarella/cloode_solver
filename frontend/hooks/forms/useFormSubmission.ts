"use client"

import { useState, useCallback } from 'react'
import { useToast } from '@/hooks/use-toast'
import { useFormPerformance } from './useFormPerformance'

interface ServiceResponse<T> {
  data: T | null
  error: string | null
  success: boolean
}

interface UseFormSubmissionOptions<T, R = any> {
  onSubmit: (data: T) => Promise<ServiceResponse<R> | R>
  onSuccess?: (result: R) => void
  onError?: (error: Error) => void
  successMessage?: string
  errorMessage?: string
  formName: string
}

export function useFormSubmission<T, R = any>({
  onSubmit,
  onSuccess,
  onError,
  successMessage = "Operation completed successfully",
  errorMessage = "An error occurred",
  formName
}: UseFormSubmissionOptions<T, R>) {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const { toast } = useToast()
  const { startSubmission, endSubmission, trackError } = useFormPerformance(formName)

  const handleSubmit = useCallback(async (data: T) => {
    setSubmitting(true)
    setError(null)
    startSubmission()

    try {
      const result = await onSubmit(data)
      
      // Handle both ServiceResponse and direct returns
      let actualResult: R
      if (result && typeof result === 'object' && 'success' in result && 'data' in result) {
        const serviceResult = result as ServiceResponse<R>
        if (serviceResult.success && serviceResult.data !== null) {
          actualResult = serviceResult.data
        } else {
          throw new Error(serviceResult.error || errorMessage)
        }
      } else {
        actualResult = result as R
      }
      
      toast({
        title: "Success",
        description: successMessage,
      })

      if (onSuccess) {
        onSuccess(actualResult)
      }

      return actualResult
    } catch (err) {
      const error = err as Error
      setError(error)
      trackError()
      
      toast({
        title: "Error",
        description: error.message || errorMessage,
        variant: "destructive"
      })

      if (onError) {
        onError(error)
      }

      throw error
    } finally {
      setSubmitting(false)
      endSubmission()
    }
  }, [onSubmit, onSuccess, onError, successMessage, errorMessage, toast, startSubmission, endSubmission, trackError, formName])

  const reset = useCallback(() => {
    setError(null)
  }, [])

  return {
    handleSubmit,
    submitting,
    error,
    reset
  }
}