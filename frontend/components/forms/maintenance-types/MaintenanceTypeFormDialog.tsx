import { UseFormReturn } from 'react-hook-form'
import { Button } from '@/components/ui/button'
import { CardContent } from '@/components/ui/card'
import { Loader2 } from 'lucide-react'
import { MaintenanceTypeBasicInfo } from './MaintenanceTypeBasicInfo'
import { MaintenanceTypeCheckboxes } from './MaintenanceTypeCheckboxes'
import type { MaintenanceTypeFormData } from '@/lib/schemas/maintenance-type.schema'

interface MaintenanceTypeFormDialogProps {
  form: UseFormReturn<MaintenanceTypeFormData>
  editingId: string | null
  isSubmitting: boolean
  onSubmit: (data: MaintenanceTypeFormData) => Promise<void>
  onCancel: () => void
  onFieldInteraction: (event: string, fieldId: string, value?: any) => void
}

export function MaintenanceTypeFormDialog({
  form,
  editingId,
  isSubmitting,
  onSubmit,
  onCancel,
  onFieldInteraction
}: MaintenanceTypeFormDialogProps) {
  const { handleSubmit, formState: { isValid } } = form

  return (
    <CardContent>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <MaintenanceTypeBasicInfo
          form={form}
          onFieldInteraction={onFieldInteraction}
        />
        
        <MaintenanceTypeCheckboxes
          form={form}
          onFieldInteraction={onFieldInteraction}
        />

        <div className="flex justify-end space-x-2 pt-4">
          {editingId && (
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          )}
          <Button 
            type="submit" 
            disabled={isSubmitting || !isValid}
            onClick={() => onFieldInteraction('click', 'submit_button')}
          >
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {editingId ? 'Update' : 'Create'} Maintenance Type
          </Button>
        </div>
      </form>
    </CardContent>
  )
}