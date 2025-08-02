"use client"

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { TimeInput } from '@/components/ui/time-input'
import { Loader2 } from 'lucide-react'

interface BusinessCalendarFormFieldsProps {
  register: any
  setValue: any
  watch: any
  errors: any
  editingId: string | null
  isSubmitting: boolean
  daysOfWeek: Array<{ bit: number; label: string; abbr: string }>
  onCancel: () => void
  onInteraction?: (type: string, field: string) => void
}

export function BusinessCalendarFormFields({
  register,
  setValue,
  watch,
  errors,
  editingId,
  isSubmitting,
  daysOfWeek,
  onCancel,
  onInteraction
}: BusinessCalendarFormFieldsProps) {
  const trackInteraction = (type: string, field: string) => {
    onInteraction?.(type, field)
  }

  return (
    <form className="space-y-4" role="form" aria-label="Business calendar form">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Name - Required */}
        <div className="space-y-2">
          <Label htmlFor="name">Calendar Name *</Label>
          <Input
            id="name"
            {...register('name', { 
              required: 'Calendar name is required',
              maxLength: { value: 255, message: 'Name must be 255 characters or less' }
            })}
            placeholder="e.g., Standard Business Calendar"
            onFocus={() => trackInteraction('focus', 'name')}
            onBlur={() => {
              const value = (document.getElementById('name') as HTMLInputElement)?.value
              if (value && onInteraction) {
                trackInteraction('validation', value.length > 255 ? 'name_error' : 'name_valid')
              }
            }}
            onChange={() => trackInteraction('change', 'name')}
            aria-describedby={errors.name ? "name-error" : undefined}
          />
          {errors.name && <p id="name-error" className="text-sm text-red-600" role="alert">{errors.name.message}</p>}
        </div>

        {/* Timezone */}
        <div className="space-y-2">
          <Label htmlFor="timezone">Timezone</Label>
          <Input
            id="timezone"
            {...register('timezone')}
            placeholder="e.g., UTC, America/New_York, Europe/London"
            onFocus={() => trackInteraction('focus', 'timezone')}
            onChange={() => trackInteraction('change', 'timezone')}
          />
        </div>

        {/* Start Time */}
        <TimeInput
          label="Default Start Time"
          value={watch('default_start_time') || 32}
          onChange={(index) => {
            setValue('default_start_time', index)
            trackInteraction('click', 'time-input#default_start_time')
          }}
          id="default_start_time"
          placeholder="Select start time"
          helperText="Default working hours start time for this calendar"
          required
        />

        {/* End Time */}
        <TimeInput
          label="Default End Time"
          value={watch('default_end_time') || 64}
          onChange={(index) => {
            setValue('default_end_time', index)
            trackInteraction('click', 'time-input#default_end_time')
          }}
          id="default_end_time"
          placeholder="Select end time"
          helperText="Default working hours end time for this calendar"
          required
        />
      </div>

      {/* Description */}
      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          {...register('description')}
          placeholder="Calendar description and usage notes"
          rows={3}
          onFocus={() => trackInteraction('focus', 'description')}
          onChange={() => trackInteraction('change', 'description')}
        />
      </div>

      {/* Working Days */}
      <div className="space-y-2">
        <Label>Working Days</Label>
        <div className="grid grid-cols-7 gap-2">
          {daysOfWeek.map((day, index) => (
            <div key={day.label} className="flex items-center space-x-2">
              <Checkbox
                id={`working_day_${index}`}
                checked={(watch('working_days') || [])[index] || false}
                onCheckedChange={(checked) => {
                  const currentDays = watch('working_days') || []
                  const newDays = [...currentDays]
                  newDays[index] = checked as boolean
                  setValue('working_days', newDays)
                  trackInteraction('click', `checkbox#working_day_${index}`)
                }}
              />
              <Label htmlFor={`working_day_${index}`} className="text-sm">
                {day.abbr}
              </Label>
            </div>
          ))}
        </div>
      </div>

      {/* Checkboxes */}
      <div className="flex flex-col space-y-4">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="is_default"
            checked={watch('is_default')}
            onCheckedChange={(checked) => {
              setValue('is_default', checked as boolean)
              trackInteraction('click', 'checkbox#is_default')
            }}
          />
          <Label htmlFor="is_default">Default Calendar</Label>
          <p className="text-xs text-gray-500 ml-2">Use as default for new departments and resources</p>
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox
            id="is_active"
            checked={watch('is_active')}
            onCheckedChange={(checked) => {
              setValue('is_active', checked as boolean)
              trackInteraction('click', 'checkbox#is_active')
            }}
          />
          <Label htmlFor="is_active">Active</Label>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-2 pt-4">
        {editingId && (
          <Button 
            type="button" 
            variant="outline" 
            onClick={() => {
              onCancel()
              trackInteraction('click', 'button#cancel')
            }}
          >
            Cancel
          </Button>
        )}
        <Button 
          type="submit" 
          disabled={isSubmitting}
          onClick={() => trackInteraction('click', 'button#submit')}
        >
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {editingId ? 'Update' : 'Create'} Calendar
        </Button>
      </div>
    </form>
  )
}
