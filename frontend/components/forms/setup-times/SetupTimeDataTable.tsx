import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/forms/common/DataTable'
import { BulkActionsToolbar } from '@/components/forms/common/BulkActionsToolbar'
import type { SetupTime } from '@/hooks/forms/useSetupTimeData'
import type { ColumnDef } from '@/components/forms/common/DataTable'
import { Button } from '@/components/ui/button'
import { Edit, Trash2 } from 'lucide-react'

interface SetupTimeDataTableProps {
  setupTimes: SetupTime[]
  loading: boolean
  onEdit: (setupTime: SetupTime) => void
  onDelete: (id: string) => void
}

export function SetupTimeDataTable({
  setupTimes,
  loading,
  onEdit,
  onDelete
}: SetupTimeDataTableProps) {
  const columns: ColumnDef<SetupTime>[] = [
    {
      key: 'from_task',
      header: 'From Task',
      accessor: (setupTime) => (
        <div className="text-sm">
          <div className="font-medium">{setupTime.from_task?.name || 'Unknown'}</div>
        </div>
      ),
      sortable: true,
      filterable: true
    },
    {
      key: 'to_task',
      header: 'To Task',
      accessor: (setupTime) => (
        <div className="text-sm">
          <div className="font-medium">{setupTime.to_task?.name || 'Unknown'}</div>
        </div>
      ),
      sortable: true,
      filterable: true
    },
    {
      key: 'machine',
      header: 'Machine',
      accessor: (setupTime) => setupTime.machine?.name || 'Unknown',
      sortable: true,
      filterable: true
    },
    {
      key: 'time',
      header: 'Time (min)',
      accessor: (setupTime) => (
        <span className="font-medium">{setupTime.setup_time_minutes}</span>
      ),
      sortable: true,
      width: 'w-24'
    },
    {
      key: 'type',
      header: 'Type',
      accessor: (setupTime) => (
        <span className="capitalize">
          {setupTime.setup_type?.replace('_', ' ') || 'Standard'}
        </span>
      ),
      sortable: true,
      filterable: true
    },
    {
      key: 'complexity',
      header: 'Complexity',
      accessor: (setupTime) => (
        <span className="capitalize">
          {setupTime.complexity_level?.replace('_', ' ') || 'Simple'}
        </span>
      ),
      sortable: true,
      filterable: true
    },
    {
      key: 'cost',
      header: 'Cost',
      accessor: (setupTime) => `$${setupTime.setup_cost?.toFixed(2) || '0.00'}`,
      sortable: true,
      width: 'w-24'
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: (setupTime) => (
        <div className="flex space-x-1">
          <Button
            size="sm"
            variant="outline"
            onClick={() => onEdit(setupTime)}
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              if (confirm('Are you sure you want to delete this setup time?')) {
                onDelete(setupTime.setup_time_id)
              }
            }}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
      width: 'w-24'
    }
  ]

  const handleBulkDelete = async (selectedItems: SetupTime[]) => {
    if (confirm(`Are you sure you want to delete ${selectedItems.length} setup times?`)) {
      for (const item of selectedItems) {
        await onDelete(item.setup_time_id)
      }
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Setup Times</CardTitle>
        <CardDescription>Manage existing setup times between template tasks</CardDescription>
      </CardHeader>
      <CardContent>
        <DataTable
          data={setupTimes}
          columns={columns}
          loading={loading}
          searchPlaceholder="Search setup times..."
          bulkActions={(selectedRows) => (
            <BulkActionsToolbar
              selectedCount={selectedRows.length}
              onBulkDelete={() => handleBulkDelete(selectedRows)}
              onClearSelection={() => {}}
            />
          )}
        />
      </CardContent>
    </Card>
  )
}