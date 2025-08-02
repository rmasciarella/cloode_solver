import { UseFormReturn } from 'react-hook-form'
import { Button } from '@/components/ui/button'
import { CardContent } from '@/components/ui/card'
import { Loader2 } from 'lucide-react'
import { SetupTimeBasicInfo } from './SetupTimeBasicInfo'
import { SetupTimeAdvancedInfo } from './SetupTimeAdvancedInfo'
import { SetupTimeCheckboxes } from './SetupTimeCheckboxes'
import type { SetupTimeFormData } from '@/lib/schemas/setup-time.schema'
import type { OptimizedTask, Machine } from '@/hooks/forms/useSetupTimeData'

interface SetupTimeFormDialogProps {
  form: UseFormReturn<SetupTimeFormData>
  templateTasks: OptimizedTask[]
  machines: Machine[]
  editingId: string | null
  isSubmitting: boolean
  onSubmit: (data: SetupTimeFormData) => Promise<void>
  onCancel: () => void
  onFieldFocus: (fieldId: string) => void
  onFieldBlur: (fieldId: string, value: any) => void
  onFieldChange: (fieldId: string, value: any) => void
}

export function SetupTimeFormDialog({
  form,
  templateTasks,
  machines,
  editingId,
  isSubmitting,
  onSubmit,
  onCancel,
  onFieldFocus,
  onFieldBlur,
  onFieldChange
}: SetupTimeFormDialogProps) {
  const { handleSubmit, watch, formState: { errors: _errors } } = form
  
  const isValid = watch('from_optimized_task_id') && 
                  watch('to_optimized_task_id') && 
                  watch('machine_resource_id')

  return (
    <CardContent>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <SetupTimeBasicInfo
          form={form}
          templateTasks={templateTasks}
          machines={machines}
          onFieldFocus={onFieldFocus}
          onFieldBlur={onFieldBlur}
          onFieldChange={onFieldChange}
        />
        
        <SetupTimeAdvancedInfo
          form={form}
          onFieldFocus={onFieldFocus}
          onFieldBlur={onFieldBlur}
          onFieldChange={onFieldChange}
        />
        
        <SetupTimeCheckboxes
          form={form}
          onFieldFocus={onFieldFocus}
          onFieldBlur={onFieldBlur}
          onFieldChange={onFieldChange}
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
          >
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {editingId ? 'Update' : 'Create'} Setup Time
          </Button>
        </div>
      </form>
    </CardContent>
  )
}