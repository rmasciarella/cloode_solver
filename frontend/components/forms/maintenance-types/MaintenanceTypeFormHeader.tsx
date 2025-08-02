import { CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface MaintenanceTypeFormHeaderProps {
  editingId: string | null
}

export function MaintenanceTypeFormHeader({ editingId }: MaintenanceTypeFormHeaderProps) {
  return (
    <CardHeader>
      <CardTitle>{editingId ? 'Edit Maintenance Type' : 'Create New Maintenance Type'}</CardTitle>
      <CardDescription>
        {editingId ? 'Update maintenance type configuration' : 'Define maintenance types for planned and emergency maintenance windows'}
      </CardDescription>
    </CardHeader>
  )
}