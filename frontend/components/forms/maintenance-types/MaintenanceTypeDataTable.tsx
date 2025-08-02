import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/forms/common/DataTable'
import { BulkActionsToolbar } from '@/components/forms/common/BulkActionsToolbar'
import type { MaintenanceType } from '@/hooks/forms/useMaintenanceTypeData'
import type { ColumnDef } from '@/components/forms/common/DataTable'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Edit, Trash2, Clock, AlertTriangle, Wrench, Ban } from 'lucide-react'

interface MaintenanceTypeDataTableProps {
  maintenanceTypes: MaintenanceType[]
  loading: boolean
  onEdit: (maintenanceType: MaintenanceType) => void
  onDelete: (id: string) => void
}

export function MaintenanceTypeDataTable({
  maintenanceTypes,
  loading,
  onEdit,
  onDelete
}: MaintenanceTypeDataTableProps) {
  const columns: ColumnDef<MaintenanceType>[] = [
    {
      key: 'name',
      header: 'Name',
      accessor: (type) => (
        <div className="flex items-center space-x-2">
          {type.is_emergency ? (
            <AlertTriangle className="h-4 w-4 text-red-500" />
          ) : type.is_preventive ? (
            <Wrench className="h-4 w-4 text-blue-500" />
          ) : (
            <Clock className="h-4 w-4 text-gray-500" />
          )}
          <span className="font-medium">{type.name}</span>
        </div>
      ),
      sortable: true,
      filterable: true
    },
    {
      key: 'description',
      header: 'Description',
      accessor: (type) => (
        <div className="max-w-xs truncate text-sm text-gray-600">
          {type.description || '-'}
        </div>
      ),
      filterable: true
    },
    {
      key: 'type',
      header: 'Type',
      accessor: (type) => (
        <div className="flex gap-1">
          {type.is_preventive && (
            <Badge variant="default" className="text-xs">Preventive</Badge>
          )}
          {type.is_emergency && (
            <Badge variant="destructive" className="text-xs">Emergency</Badge>
          )}
          {!type.is_preventive && !type.is_emergency && (
            <Badge variant="secondary" className="text-xs">Other</Badge>
          )}
        </div>
      ),
      filterable: true
    },
    {
      key: 'duration',
      header: 'Duration',
      accessor: (type) => `${type.typical_duration_hours}h`,
      sortable: true,
      width: 'w-20'
    },
    {
      key: 'impact',
      header: 'Production Impact',
      accessor: (type) => (
        <div className="flex items-center gap-2">
          {type.blocks_production && (
            <Badge variant="destructive" className="text-xs">
              <Ban className="h-3 w-3 mr-1" />
              Blocks
            </Badge>
          )}
          {type.requires_shutdown && (
            <Badge variant="outline" className="text-xs">Shutdown</Badge>
          )}
          {!type.blocks_production && !type.requires_shutdown && (
            <span className="text-sm text-gray-500">Minimal</span>
          )}
        </div>
      ),
      filterable: true
    },
    {
      key: 'requirements',
      header: 'Requirements',
      accessor: (type) => (
        <div className="text-sm space-y-1">
          {type.required_skill_level && (
            <div>Skill: {type.required_skill_level}</div>
          )}
          {type.requires_external_vendor && (
            <Badge variant="outline" className="text-xs">External Vendor</Badge>
          )}
        </div>
      )
    },
    {
      key: 'override',
      header: 'Override',
      accessor: (type) => (
        type.allows_emergency_override ? (
          <Badge variant="secondary" className="text-xs">Allowed</Badge>
        ) : (
          <span className="text-sm text-gray-400">-</span>
        )
      ),
      width: 'w-24'
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: (type) => (
        <div className="flex space-x-1">
          <Button
            size="sm"
            variant="outline"
            onClick={() => onEdit(type)}
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              if (confirm('Are you sure you want to delete this maintenance type?')) {
                onDelete(type.maintenance_type_id)
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

  const handleBulkDelete = async (selectedItems: MaintenanceType[]) => {
    if (confirm(`Are you sure you want to delete ${selectedItems.length} maintenance types?`)) {
      for (const item of selectedItems) {
        await onDelete(item.maintenance_type_id)
      }
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Maintenance Types</CardTitle>
        <CardDescription>Manage maintenance types and their scheduling characteristics</CardDescription>
      </CardHeader>
      <CardContent>
        <DataTable
          data={maintenanceTypes}
          columns={columns}
          loading={loading}
          searchPlaceholder="Search maintenance types..."
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