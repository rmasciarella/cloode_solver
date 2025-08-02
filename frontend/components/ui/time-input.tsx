"use client"

import React, { useState, useEffect } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { generateTimeSlots, indexToTime12, isValidTimeIndex } from '@/lib/timeUtils'

interface TimeInputProps {
  label: string
  value: number
  onChange: (index: number) => void
  id?: string | undefined
  placeholder?: string | undefined
  disabled?: boolean | undefined
  required?: boolean | undefined
  helperText?: string | undefined
  className?: string | undefined
}

export function TimeInput({
  label,
  value,
  onChange,
  id,
  placeholder = "Select time",
  disabled = false,
  required = false,
  helperText,
  className = ""
}: TimeInputProps) {
  const [timeSlots] = useState(() => generateTimeSlots())
  
  const handleTimeChange = (timeValue: string) => {
    const index = parseInt(timeValue, 10)
    if (isValidTimeIndex(index)) {
      onChange(index)
    }
  }

  const displayValue = isValidTimeIndex(value) ? indexToTime12(value) : ''
  
  return (
    <div className={`space-y-2 ${className}`}>
      <Label htmlFor={id}>
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </Label>
      
      <Select
        value={isValidTimeIndex(value) ? value.toString() : undefined}
        onValueChange={handleTimeChange}
        disabled={disabled}
      >
        <SelectTrigger id={id}>
          <SelectValue placeholder={placeholder}>
            {displayValue || placeholder}
          </SelectValue>
        </SelectTrigger>
        <SelectContent className="max-h-60">
          {timeSlots.map((slot) => (
            <SelectItem key={slot.index} value={slot.index.toString()}>
              <div className="flex justify-between items-center w-full">
                <span className="font-medium">{slot.time12}</span>
                <span className="text-gray-500 text-sm ml-4">{slot.time24}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      {helperText && (
        <p className="text-xs text-gray-500">{helperText}</p>
      )}
      
      {isValidTimeIndex(value) && (
        <p className="text-xs text-gray-600">
          Current value: <span className="font-medium">{displayValue}</span> (15-minute units from midnight)
        </p>
      )}
    </div>
  )
}

export default TimeInput