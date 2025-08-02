import { CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface SetupTimeFormHeaderProps {
  editingId: string | null
}

export function SetupTimeFormHeader({ editingId }: SetupTimeFormHeaderProps) {
  return (
    <CardHeader>
      <CardTitle>{editingId ? 'Edit Setup Time' : 'Create New Setup Time'}</CardTitle>
      <CardDescription>
        {editingId ? 'Update setup time configuration' : 'Define setup times between template tasks for constraint generation'}
      </CardDescription>
    </CardHeader>
  )
}