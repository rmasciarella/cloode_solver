"use client"

import { ReactNode } from 'react'
import { UseFormReturn, FieldErrors, FieldValues } from 'react-hook-form'
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'

// Common form footer with submit/cancel buttons
interface FormFooterProps {
  isSubmitting: boolean
  onCancel: () => void
  submitLabel?: string
  isEditing?: boolean
}

export function FormFooter({ 
  isSubmitting, 
  onCancel, 
  submitLabel = "Submit",
  isEditing = false 
}: FormFooterProps) {
  return (
    <div className="flex gap-3 mt-6">
      <Button
        type="submit"
        disabled={isSubmitting}
        aria-busy={isSubmitting}
      >
        {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isEditing ? `Update ${submitLabel}` : `Create ${submitLabel}`}
      </Button>
      <Button
        type="button"
        variant="outline"
        onClick={onCancel}
        disabled={isSubmitting}
      >
        Cancel
      </Button>
    </div>
  )
}

// Empty state component
interface EmptyStateProps {
  title: string
  description?: string
  action?: ReactNode
  icon?: ReactNode
}

export function EmptyState({ title, description, action, icon }: EmptyStateProps) {
  return (
    <div className="text-center py-12">
      {icon && <div className="mx-auto w-12 h-12 text-gray-400 mb-4">{icon}</div>}
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      {description && <p className="text-sm text-gray-500 mb-4">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}

// Common status badge colors
export const statusColors = {
  active: 'default',
  inactive: 'secondary',
  pending: 'outline',
  completed: 'default',
  failed: 'destructive',
  warning: 'destructive',
  info: 'secondary'
} as const

// Common complexity/level colors
export const levelColors = {
  basic: 'bg-green-100 text-green-800',
  intermediate: 'bg-yellow-100 text-yellow-800',
  advanced: 'bg-orange-100 text-orange-800',
  expert: 'bg-red-100 text-red-800',
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800'
} as const

// Format currency
export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency
  }).format(amount)
}

// Format duration
export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes} min`
  }
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (mins === 0) {
    return `${hours}h`
  }
  return `${hours}h ${mins}m`
}

// Format date
export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }).format(new Date(date))
}

// Format time
export function formatTime(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit'
  }).format(new Date(date))
}

// Get error message from form field
export function getFieldError<T extends FieldValues>(
  errors: FieldErrors<T>,
  fieldName: keyof T
): string | undefined {
  const error = errors[fieldName]
  if (!error) return undefined
  
  // Handle different error message types from react-hook-form
  if (typeof error.message === 'string') {
    return error.message
  }
  
  // For complex error types, try to extract a string message
  if (error.message && typeof error.message === 'object' && 'message' in error.message) {
    return String(error.message.message)
  }
  
  // Fallback to a generic error message
  return 'Validation error'
}

// Common select options
export const booleanOptions = [
  { value: 'true', label: 'Yes' },
  { value: 'false', label: 'No' }
]

export const statusOptions = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' }
]

export const priorityOptions = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' }
]

export const frequencyOptions = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'yearly', label: 'Yearly' }
]

// Common validation patterns
export const validationPatterns = {
  code: {
    pattern: /^[A-Z0-9-_]+$/,
    message: 'Must contain only uppercase letters, numbers, hyphens, and underscores'
  },
  email: {
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    message: 'Must be a valid email address'
  },
  phone: {
    pattern: /^\+?[\d\s-()]+$/,
    message: 'Must be a valid phone number'
  },
  url: {
    pattern: /^https?:\/\/.+$/,
    message: 'Must be a valid URL starting with http:// or https://'
  },
  alphanumeric: {
    pattern: /^[a-zA-Z0-9]+$/,
    message: 'Must contain only letters and numbers'
  }
}

// Common field validators
export const validators = {
  required: (fieldName: string) => ({
    required: `${fieldName} is required`
  }),
  
  minLength: (fieldName: string, min: number) => ({
    minLength: {
      value: min,
      message: `${fieldName} must be at least ${min} characters`
    }
  }),
  
  maxLength: (fieldName: string, max: number) => ({
    maxLength: {
      value: max,
      message: `${fieldName} must be no more than ${max} characters`
    }
  }),
  
  min: (fieldName: string, min: number) => ({
    min: {
      value: min,
      message: `${fieldName} must be at least ${min}`
    }
  }),
  
  max: (fieldName: string, max: number) => ({
    max: {
      value: max,
      message: `${fieldName} must be no more than ${max}`
    }
  }),
  
  pattern: (fieldName: string, pattern: RegExp, message?: string) => ({
    pattern: {
      value: pattern,
      message: message || `${fieldName} format is invalid`
    }
  })
}