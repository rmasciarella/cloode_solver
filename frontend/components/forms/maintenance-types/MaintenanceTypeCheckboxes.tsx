import { UseFormReturn } from 'react-hook-form'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import type { MaintenanceTypeFormData } from '@/lib/schemas/maintenance-type.schema'

interface MaintenanceTypeCheckboxesProps {
  form: UseFormReturn<MaintenanceTypeFormData>
  onFieldInteraction: (event: string, fieldId: string, value?: any) => void
}

export function MaintenanceTypeCheckboxes({
  form,
  onFieldInteraction
}: MaintenanceTypeCheckboxesProps) {
  const { setValue, watch } = form

  const checkboxFields = [
    {
      id: 'is_preventive',
      label: 'Preventive Maintenance',
      description: 'Scheduled maintenance to prevent failures'
    },
    {
      id: 'is_emergency',
      label: 'Emergency Maintenance',
      description: 'Unplanned maintenance for critical issues'
    },
    {
      id: 'blocks_production',
      label: 'Blocks Production',
      description: 'Stops production lines during maintenance'
    },
    {
      id: 'allows_emergency_override',
      label: 'Allows Emergency Override',
      description: 'Can be interrupted for critical production needs'
    },
    {
      id: 'requires_shutdown',
      label: 'Requires Shutdown',
      description: 'Requires complete machine shutdown'
    },
    {
      id: 'requires_external_vendor',
      label: 'Requires External Vendor',
      description: 'Needs external service provider'
    }
  ]

  return (
    <div className="space-y-4">
      <Label>Maintenance Characteristics</Label>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {checkboxFields.map((field) => (
          <div key={field.id} className="flex items-start space-x-2">
            <Checkbox
              id={field.id}
              checked={watch(field.id as keyof MaintenanceTypeFormData) as boolean}
              onCheckedChange={(checked) => {
                setValue(field.id as keyof MaintenanceTypeFormData, checked as boolean)
                onFieldInteraction('change', field.id, checked)
              }}
              onFocus={() => onFieldInteraction('focus', field.id)}
              onBlur={() => onFieldInteraction('blur', field.id, watch(field.id as keyof MaintenanceTypeFormData))}
            />
            <div className="space-y-0.5">
              <Label htmlFor={field.id} className="font-normal cursor-pointer">
                {field.label}
              </Label>
              <p className="text-xs text-muted-foreground">
                {field.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}