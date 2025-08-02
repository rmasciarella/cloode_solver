"use client"

import { UseFormReturn } from 'react-hook-form'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface SkillFormData {
  name: string
  description: string
  category: string
  department_id: string
  complexity_level: string
  training_hours_required: number
  certification_required: boolean
  certification_expires_after_months: number
  market_hourly_rate: number
  skill_scarcity_level: string
  is_active: boolean
}

interface SkillFormFieldsProps {
  form: UseFormReturn<SkillFormData>
  departments: Array<{ department_id: string; name: string; code: string }>
  onFieldFocus?: (fieldName: string) => void
  onInteraction?: () => void
}

const complexityLevels = [
  { value: 'basic', label: 'Basic' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
  { value: 'expert', label: 'Expert' }
]

const scarcityLevels = [
  { value: 'common', label: 'Common' },
  { value: 'uncommon', label: 'Uncommon' },
  { value: 'rare', label: 'Rare' },
  { value: 'critical', label: 'Critical' }
]

const skillCategories = [
  'mechanical',
  'electrical',
  'quality',
  'assembly',
  'testing',
  'machining',
  'splicing',
  'alignment',
  'cleaning'
]

export function SkillFormFields({ 
  form, 
  departments, 
  onFieldFocus, 
  onInteraction 
}: SkillFormFieldsProps) {
  const { register, formState: { errors }, watch, setValue } = form
  const certificationRequired = watch('certification_required')

  const handleFieldFocus = (fieldName: string) => {
    onFieldFocus?.(fieldName)
    onInteraction?.()
  }

  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Basic Information</h3>
        
        <div className="space-y-2">
          <Label htmlFor="name">Skill Name *</Label>
          <Input
            id="name"
            {...register('name', { required: 'Skill name is required' })}
            onFocus={() => handleFieldFocus('name')}
            aria-label="Skill name"
            aria-required="true"
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? "name-error" : undefined}
          />
          {errors.name && (
            <p id="name-error" className="text-sm text-red-500" role="alert">
              {errors.name.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            {...register('description')}
            onFocus={() => handleFieldFocus('description')}
            aria-label="Skill description"
            rows={3}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="category">Category *</Label>
            <Select
              value={watch('category') || ''}
              onValueChange={(value) => {
                setValue('category', value)
                onInteraction?.()
              }}
            >
              <SelectTrigger 
                id="category"
                aria-label="Skill category"
                aria-required="true"
                aria-invalid={!!errors.category}
              >
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {skillCategories.map(cat => (
                  <SelectItem key={cat} value={cat}>
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="department_id">Department *</Label>
            <Select
              value={watch('department_id') || ''}
              onValueChange={(value) => {
                setValue('department_id', value)
                onInteraction?.()
              }}
            >
              <SelectTrigger 
                id="department_id"
                aria-label="Department"
                aria-required="true"
                aria-invalid={!!errors.department_id}
              >
                <SelectValue placeholder="Select department" />
              </SelectTrigger>
              <SelectContent>
                {departments.map(dept => (
                  <SelectItem key={dept.department_id} value={dept.department_id}>
                    {dept.name} ({dept.code})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Skill Requirements */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Skill Requirements</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="complexity_level">Complexity Level *</Label>
            <Select
              value={watch('complexity_level') || ''}
              onValueChange={(value) => {
                setValue('complexity_level', value)
                onInteraction?.()
              }}
            >
              <SelectTrigger 
                id="complexity_level"
                aria-label="Complexity level"
                aria-required="true"
              >
                <SelectValue placeholder="Select level" />
              </SelectTrigger>
              <SelectContent>
                {complexityLevels.map(level => (
                  <SelectItem key={level.value} value={level.value}>
                    {level.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="training_hours_required">Training Hours Required *</Label>
            <Input
              id="training_hours_required"
              type="number"
              {...register('training_hours_required', { 
                required: 'Training hours is required',
                min: { value: 0, message: 'Must be 0 or greater' }
              })}
              onFocus={() => handleFieldFocus('training_hours_required')}
              aria-label="Training hours required"
              aria-required="true"
              aria-invalid={!!errors.training_hours_required}
            />
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="certification_required"
              checked={certificationRequired}
              onCheckedChange={(checked) => {
                setValue('certification_required', checked as boolean)
                onInteraction?.()
              }}
              aria-label="Certification required"
            />
            <Label htmlFor="certification_required">Certification Required</Label>
          </div>

          {certificationRequired && (
            <div className="space-y-2 ml-6">
              <Label htmlFor="certification_expires_after_months">
                Certification Expires After (months)
              </Label>
              <Input
                id="certification_expires_after_months"
                type="number"
                {...register('certification_expires_after_months', {
                  required: certificationRequired ? 'Expiration period is required' : false,
                  min: { value: 1, message: 'Must be at least 1 month' }
                })}
                onFocus={() => handleFieldFocus('certification_expires_after_months')}
                aria-label="Certification expiration months"
                aria-required={certificationRequired}
              />
            </div>
          )}
        </div>
      </div>

      {/* Market Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Market Information</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="market_hourly_rate">Market Hourly Rate ($)</Label>
            <Input
              id="market_hourly_rate"
              type="number"
              step="0.01"
              {...register('market_hourly_rate', {
                min: { value: 0, message: 'Must be 0 or greater' }
              })}
              onFocus={() => handleFieldFocus('market_hourly_rate')}
              aria-label="Market hourly rate"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="skill_scarcity_level">Scarcity Level *</Label>
            <Select
              value={watch('skill_scarcity_level') || ''}
              onValueChange={(value) => {
                setValue('skill_scarcity_level', value)
                onInteraction?.()
              }}
            >
              <SelectTrigger 
                id="skill_scarcity_level"
                aria-label="Skill scarcity level"
                aria-required="true"
              >
                <SelectValue placeholder="Select level" />
              </SelectTrigger>
              <SelectContent>
                {scarcityLevels.map(level => (
                  <SelectItem key={level.value} value={level.value}>
                    {level.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="flex items-center space-x-2">
        <Checkbox
          id="is_active"
          checked={watch('is_active')}
          onCheckedChange={(checked) => {
            setValue('is_active', checked as boolean)
            onInteraction?.()
          }}
          aria-label="Skill is active"
        />
        <Label htmlFor="is_active">Active</Label>
      </div>
    </div>
  )
}