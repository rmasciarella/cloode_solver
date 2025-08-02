"use client"

import { useState, useEffect, useRef } from 'react'
import { useBusinessCalendarData } from './business-calendars/useBusinessCalendarData'
import { useBusinessCalendarForm } from './business-calendars/useBusinessCalendarForm'
import { useFormPerformanceMonitoring } from '@/lib/hooks/use-form-performance'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { BusinessCalendarFormFields } from './business-calendars/BusinessCalendarFormFields'
import { BusinessCalendarsTable } from './business-calendars/BusinessCalendarsTable'
import { Button } from '@/components/ui/button'
import { Activity } from 'lucide-react'

export default function BusinessCalendarForm() {
  const {
    businessCalendars,
    loading,
    fetchBusinessCalendars
  } = useBusinessCalendarData()

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    errors,
    editingId,
    isSubmitting,
    handleEdit,
    handleDelete,
    handleCancel,
    onSubmit
  } = useBusinessCalendarForm(fetchBusinessCalendars)
  
  // Performance tracking using the correct hook
  const formPerformanceMetrics = useFormPerformanceMonitoring('BusinessCalendarForm')
  
  const formRef = useRef<HTMLFormElement>(null)
  const [showPerformanceDebug, setShowPerformanceDebug] = useState(false)
  
  // Performance debugging in development
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      const handleKeyPress = (e: KeyboardEvent) => {
        if (e.ctrlKey && e.shiftKey && e.key === 'P') {
          e.preventDefault()
          setShowPerformanceDebug(prev => !prev)
          console.log('[FORM-PERF] Performance summary:', formPerformanceMetrics.getFormSummary())
        }
      }
      
      window.addEventListener('keydown', handleKeyPress)
      return () => window.removeEventListener('keydown', handleKeyPress)
    }
    return undefined
  }, [formPerformanceMetrics])
  
  // Call finalizeMetrics on unmount to ensure metrics are recorded
  useEffect(() => {
    return () => {
      formPerformanceMetrics.finalizeMetrics()
    }
  }, [formPerformanceMetrics])

  return (
    <div className="space-y-6">
      {/* Performance Debug Panel - Development Only */}
      {process.env.NODE_ENV === 'development' && showPerformanceDebug && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Performance Debug - BusinessCalendarForm
              <Button 
                size="sm" 
                variant="ghost" 
                onClick={() => setShowPerformanceDebug(false)}
                className="ml-auto"
              >
                ×
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs space-y-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p><strong>Load Time:</strong> {formPerformanceMetrics.loadTime || 'N/A'}ms</p>
                <p><strong>Submit Time:</strong> {formPerformanceMetrics.submissionTime || 'N/A'}ms</p>
                <p><strong>Validation Time:</strong> {formPerformanceMetrics.validationTime || 'N/A'}ms</p>
              </div>
              <div>
                <p><strong>Error Count:</strong> {formPerformanceMetrics.errorCount}</p>
                <p><strong>Interactions:</strong> {formPerformanceMetrics.interactionCount}</p>
                <p><strong>High Error Rate:</strong> {formPerformanceMetrics.hasHighErrorRate ? 'Yes' : 'No'}</p>
              </div>
            </div>
            <div className="mt-2">
              <p className="text-xs text-gray-600">Press Ctrl+Shift+P to toggle this panel</p>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Form Card */}
      <Card>
        <CardHeader>
          <CardTitle>{editingId ? 'Edit Business Calendar' : 'Create New Business Calendar'}</CardTitle>
          <CardDescription>
            {editingId ? 'Update business calendar information' : 'Define working periods and schedules for departments'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form 
            ref={formRef}
            onSubmit={handleSubmit(onSubmit)} 
            className="space-y-4"
            onClick={(e) => {
              const target = e.target as HTMLElement
              if (target.tagName === 'BUTTON' || target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
                formPerformanceMetrics.trackInteraction('click', target.tagName.toLowerCase() + (target.id ? `#${target.id}` : ''))
              }
            }}
          >
            <BusinessCalendarFormFields
              register={register}
              setValue={setValue}
              watch={watch}
              errors={errors}
              editingId={editingId}
              isSubmitting={isSubmitting}
              handleCancel={handleCancel}
              formPerformanceMetrics={formPerformanceMetrics}
            />
          </form>
        </CardContent>
      </Card>

      {/* Business Calendars List */}
      <BusinessCalendarsTable
        businessCalendars={businessCalendars}
        loading={loading}
        handleEdit={handleEdit}
        handleDelete={handleDelete}
        formPerformanceMetrics={formPerformanceMetrics}
      />
    </div>
  )
}
}