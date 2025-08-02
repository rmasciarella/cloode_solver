import { UseFormReturn } from 'react-hook-form'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import type { SetupTimeFormData } from '@/lib/schemas/setup-time.schema'

interface SetupTimeCheckboxesProps {
  form: UseFormReturn<SetupTimeFormData>
  onFieldFocus: (fieldId: string) => void
  onFieldBlur: (fieldId: string, value: any) => void
  onFieldChange: (fieldId: string, value: any) => void
}

export function SetupTimeCheckboxes({
  form,
  onFieldFocus,
  onFieldBlur,
  onFieldChange
}: SetupTimeCheckboxesProps) {
  const { setValue, watch } = form

  return (
    <div className="flex flex-col space-y-4">
      <div className="flex items-center space-x-2">
        <Checkbox
          id="requires_certification"
          checked={watch('requires_certification')}
          onCheckedChange={(checked) => {
            setValue('requires_certification', checked as boolean)
            onFieldChange('requires_certification', checked)
          }}
          onFocus={() => onFieldFocus('requires_certification')}
          onBlur={() => onFieldBlur('requires_certification', watch('requires_certification'))}
        />
        <Label htmlFor="requires_certification">Requires Certification</Label>
      </div>

      <div className="flex items-center space-x-2">
        <Checkbox
          id="requires_supervisor_approval"
          checked={watch('requires_supervisor_approval')}
          onCheckedChange={(checked) => {
            setValue('requires_supervisor_approval', checked as boolean)
            onFieldChange('requires_supervisor_approval', checked)
          }}
          onFocus={() => onFieldFocus('requires_supervisor_approval')}
          onBlur={() => onFieldBlur('requires_supervisor_approval', watch('requires_supervisor_approval'))}
        />
        <Label htmlFor="requires_supervisor_approval">Requires Supervisor Approval</Label>
      </div>
    </div>
  )
}