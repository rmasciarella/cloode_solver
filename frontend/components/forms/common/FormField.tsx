"use client"

import { ReactNode, ReactElement, cloneElement } from 'react'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

interface FormFieldProps {
  id: string
  label: string
  error?: string
  required?: boolean
  description?: string
  children: ReactElement
  className?: string
}

export function FormField({
  id,
  label,
  error,
  required = false,
  description,
  children,
  className
}: FormFieldProps) {
  const fieldId = `field-${id}`
  const errorId = `${fieldId}-error`
  const descriptionId = `${fieldId}-description`

  // Clone the child element and add accessibility attributes
  const enhancedChild = cloneElement(children, {
    id: fieldId,
    'aria-label': label,
    'aria-required': required,
    'aria-invalid': !!error,
    'aria-describedby': [
      error && errorId,
      description && descriptionId
    ].filter(Boolean).join(' ') || undefined,
    ...children.props
  })

  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={fieldId}>
        {label}
        {required && <span className="text-red-500 ml-1" aria-label="required">*</span>}
      </Label>
      
      {description && (
        <p id={descriptionId} className="text-sm text-gray-500">
          {description}
        </p>
      )}
      
      {enhancedChild}
      
      {error && (
        <p id={errorId} className="text-sm text-red-500" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

// Wrapper for form sections with proper semantic HTML
interface FormSectionProps {
  title: string
  description?: string
  children: ReactNode
  className?: string
}

export function FormSection({
  title,
  description,
  children,
  className
}: FormSectionProps) {
  return (
    <fieldset className={cn("space-y-4", className)}>
      <legend className="text-lg font-medium">
        {title}
        {description && (
          <p className="text-sm text-gray-500 mt-1 font-normal">
            {description}
          </p>
        )}
      </legend>
      {children}
    </fieldset>
  )
}

// Skip link component for keyboard navigation
export function SkipLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a
      href={href}
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-white px-4 py-2 rounded shadow-lg z-50"
    >
      {children}
    </a>
  )
}

// Announce component for screen reader announcements
interface AnnounceProps {
  message: string
  priority?: 'polite' | 'assertive'
  atomic?: boolean
}

export function Announce({ message, priority = 'polite', atomic = true }: AnnounceProps) {
  return (
    <div
      role="status"
      aria-live={priority}
      aria-atomic={atomic}
      className="sr-only"
    >
      {message}
    </div>
  )
}