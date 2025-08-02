import { UseFormReturn } from 'react-hook-form'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { setupTypes, complexityLevels, skillLevels, type SetupTimeFormData } from '@/lib/schemas/setup-time.schema'

interface SetupTimeAdvancedInfoProps {
  form: UseFormReturn<SetupTimeFormData>
  onFieldFocus: (fieldId: string) => void
  onFieldBlur: (fieldId: string, value: any) => void
  onFieldChange: (fieldId: string, value: any) => void
}

export function SetupTimeAdvancedInfo({
  form,
  onFieldFocus,
  onFieldBlur,
  onFieldChange
}: SetupTimeAdvancedInfoProps) {
  const { register, setValue, watch, formState: { errors } } = form

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label htmlFor="setup_type">Setup Type</Label>
        <Select 
          value={watch('setup_type')}
          onValueChange={(value) => {
            setValue('setup_type', value)
            onFieldChange('setup_type', value)
          }}
          onOpenChange={(open) => {
            if (open) onFieldFocus('setup_type')
            else onFieldBlur('setup_type', watch('setup_type'))
          }}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select setup type" />
          </SelectTrigger>
          <SelectContent>
            {setupTypes.map((type) => (
              <SelectItem key={type.value} value={type.value}>
                {type.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="complexity_level">Complexity Level</Label>
        <Select 
          value={watch('complexity_level')}
          onValueChange={(value) => {
            setValue('complexity_level', value)
            onFieldChange('complexity_level', value)
          }}
          onOpenChange={(open) => {
            if (open) onFieldFocus('complexity_level')
            else onFieldBlur('complexity_level', watch('complexity_level'))
          }}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select complexity" />
          </SelectTrigger>
          <SelectContent>
            {complexityLevels.map((level) => (
              <SelectItem key={level.value} value={level.value}>
                {level.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="requires_operator_skill">Required Operator Skill</Label>
        <Select 
          value={watch('requires_operator_skill') || 'none'}
          onValueChange={(value) => {
            setValue('requires_operator_skill', value === 'none' ? '' : value)
            onFieldChange('requires_operator_skill', value)
          }}
          onOpenChange={(open) => {
            if (open) onFieldFocus('requires_operator_skill')
            else onFieldBlur('requires_operator_skill', watch('requires_operator_skill'))
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

      <div className="space-y-2">
        <Label htmlFor="setup_cost">Setup Cost ($)</Label>
        <Input
          id="setup_cost"
          type="number"
          min="0"
          step="0.01"
          {...register('setup_cost', { valueAsNumber: true })}
          onFocus={() => onFieldFocus('setup_cost')}
          onBlur={(e) => onFieldBlur('setup_cost', parseFloat(e.target.value) || 0)}
          onChange={(e) => onFieldChange('setup_cost', parseFloat(e.target.value) || 0)}
        />
        {errors.setup_cost && (
          <p className="text-sm text-red-600">{errors.setup_cost.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="efficiency_impact_percent">Efficiency Impact (%)</Label>
        <Input
          id="efficiency_impact_percent"
          type="number"
          min="0"
          max="100"
          step="0.1"
          {...register('efficiency_impact_percent', { valueAsNumber: true })}
          onFocus={() => onFieldFocus('efficiency_impact_percent')}
          onBlur={(e) => onFieldBlur('efficiency_impact_percent', parseFloat(e.target.value) || 0)}
          onChange={(e) => onFieldChange('efficiency_impact_percent', parseFloat(e.target.value) || 0)}
        />
        {errors.efficiency_impact_percent && (
          <p className="text-sm text-red-600">{errors.efficiency_impact_percent.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="product_family_from">Product Family From</Label>
        <Input
          id="product_family_from"
          {...register('product_family_from')}
          placeholder="e.g., Product A, Family X"
          onFocus={() => onFieldFocus('product_family_from')}
          onBlur={(e) => onFieldBlur('product_family_from', e.target.value)}
          onChange={(e) => onFieldChange('product_family_from', e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="product_family_to">Product Family To</Label>
        <Input
          id="product_family_to"
          {...register('product_family_to')}
          placeholder="e.g., Product B, Family Y"
          onFocus={() => onFieldFocus('product_family_to')}
          onBlur={(e) => onFieldBlur('product_family_to', e.target.value)}
          onChange={(e) => onFieldChange('product_family_to', e.target.value)}
        />
      </div>
    </div>
  )
}