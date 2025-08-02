import { UseFormReturn } from 'react-hook-form'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { skillLevels, type MaintenanceTypeFormData } from '@/lib/schemas/maintenance-type.schema'

interface MaintenanceTypeBasicInfoProps {
  form: UseFormReturn<MaintenanceTypeFormData>
  onFieldInteraction: (event: string, fieldId: string, value?: any) => void
}

export function MaintenanceTypeBasicInfo({
  form,
  onFieldInteraction
}: MaintenanceTypeBasicInfoProps) {
  const { register, setValue, watch, formState: { errors } } = form

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label htmlFor="name">Maintenance Type Name *</Label>
        <Input
          id="name"
          {...register('name')}
          placeholder="e.g., Monthly Preventive"
          onFocus={() => onFieldInteraction('focus', 'name')}
          onBlur={(e) => onFieldInteraction('blur', 'name', e.target.value)}
          onChange={(e) => onFieldInteraction('change', 'name', e.target.value)}
        />
        {errors.name && (
          <p className="text-sm text-red-600">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="typical_duration_hours">Typical Duration (hours) *</Label>
        <Input
          id="typical_duration_hours"
          type="number"
          min="0.1"
          step="0.1"
          {...register('typical_duration_hours', { valueAsNumber: true })}
          onFocus={() => onFieldInteraction('focus', 'typical_duration_hours')}
          onBlur={(e) => onFieldInteraction('blur', 'typical_duration_hours', parseFloat(e.target.value) || 0)}
          onChange={(e) => onFieldInteraction('change', 'typical_duration_hours', parseFloat(e.target.value) || 0)}
        />
        {errors.typical_duration_hours && (
          <p className="text-sm text-red-600">{errors.typical_duration_hours.message}</p>
        )}
      </div>

      <div className="space-y-2 md:col-span-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          {...register('description')}
          placeholder="Describe the maintenance type and its purpose"
          className="min-h-[100px]"
          onFocus={() => onFieldInteraction('focus', 'description')}
          onBlur={(e) => onFieldInteraction('blur', 'description', e.target.value)}
          onChange={(e) => onFieldInteraction('change', 'description', e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="required_skill_level">Required Skill Level</Label>
        <Select 
          value={watch('required_skill_level') || 'none'}
          onValueChange={(value) => {
            setValue('required_skill_level', value === 'none' ? '' : value)
            onFieldInteraction('change', 'required_skill_level', value)
          }}
          onOpenChange={(open) => {
            if (open) onFieldInteraction('focus', 'required_skill_level')
            else onFieldInteraction('blur', 'required_skill_level', watch('required_skill_level'))
          }}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select skill level" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">No Specific Requirement</SelectItem>
            {skillLevels.map((skill) => (
              <SelectItem key={skill.value} value={skill.value}>
                {skill.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}