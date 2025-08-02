"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { businessCalendarService } from '@/lib/services'
import { useToast } from '@/hooks/use-toast'

const daysOfWeek = [
  { bit: 0, label: 'Monday', abbr: 'Mon' },
  { bit: 1, label: 'Tuesday', abbr: 'Tue' },
  { bit: 2, label: 'Wednesday', abbr: 'Wed' },
  { bit: 3, label: 'Thursday', abbr: 'Thu' },
  { bit: 4, label: 'Friday', abbr: 'Fri' },
  { bit: 5, label: 'Saturday', abbr: 'Sat' },
  { bit: 6, label: 'Sunday', abbr: 'Sun' }
]

export function useBusinessCalendarForm() {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const form = useForm({
    defaultValues: {
      name: '',
      description: '',
      timezone: 'UTC',
      default_start_time: 32, // 8 AM
      default_end_time: 64,   // 4 PM
      working_days: [true, true, true, true, true, false, false], // Mon-Fri
      is_default: false,
      is_active: true
    }
  })

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = form

  const workingDaysMaskToArray = (mask: number): boolean[] => {
    return daysOfWeek.map(day => Boolean(mask & (1 << day.bit)))
  }

  const arrayToWorkingDaysMask = (days: boolean[]): number => {
    return days.reduce((mask, isWorking, index) => {
      return isWorking ? mask | (1 << index) : mask
    }, 0)
  }

  const onSubmit = async (data: any, onSuccess?: () => void) => {
    setIsSubmitting(true)
    
    try {
      const formData = {
        name: data.name,
        description: data.description || null,
        timezone: data.timezone,
        default_start_time: data.default_start_time,
        default_end_time: data.default_end_time,
        working_days_mask: arrayToWorkingDaysMask(data.working_days),
        is_default: data.is_default,
        is_active: data.is_active
      }

      if (editingId) {
        const response = await businessCalendarService.update(editingId, formData)
        if (!response.success) {
          throw new Error(response.error || 'Failed to update business calendar')
        }

        toast({
          title: "Success",
          description: "Business calendar updated successfully"
        })
      } else {
        const response = await businessCalendarService.create(formData)
        if (!response.success) {
          throw new Error(response.error || 'Failed to create business calendar')
        }

        toast({
          title: "Success",
          description: "Business calendar created successfully"
        })
      }

      reset()
      setEditingId(null)
      onSuccess?.()
    } catch (error) {
      console.error('Error saving business calendar:', error)
      toast({
        title: "Error",
        description: "Failed to save business calendar",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = (calendar: any) => {
    setEditingId(calendar.calendar_id)
    setValue('name', calendar.name)
    setValue('description', calendar.description || '')
    setValue('timezone', calendar.timezone)
    setValue('default_start_time', calendar.default_start_time)
    setValue('default_end_time', calendar.default_end_time)
    setValue('working_days', workingDaysMaskToArray(calendar.working_days_mask))
    setValue('is_default', calendar.is_default)
    setValue('is_active', calendar.is_active)
  }

  const handleDelete = async (id: string, onSuccess?: () => void) => {
    if (!confirm('Are you sure you want to delete this business calendar?')) return

    try {
      const response = await businessCalendarService.delete(id)
      if (!response.success) {
        throw new Error(response.error || 'Failed to delete business calendar')
      }

      toast({
        title: "Success",
        description: "Business calendar deleted successfully"
      })
      onSuccess?.()
    } catch (error) {
      console.error('Error deleting business calendar:', error)
      toast({
        title: "Error",
        description: "Failed to delete business calendar",
        variant: "destructive"
      })
    }
  }

  const handleCancel = () => {
    reset()
    setEditingId(null)
  }

  return {
    form,
    register,
    handleSubmit: (onSuccess?: () => void) => handleSubmit((data) => onSubmit(data, onSuccess)),
    reset,
    setValue,
    watch,
    errors,
    editingId,
    isSubmitting,
    handleEdit,
    handleDelete,
    handleCancel,
    workingDaysMaskToArray,
    arrayToWorkingDaysMask,
    daysOfWeek
  }
}
