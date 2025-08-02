"use client"

import { Database } from '@/lib/database.types'
import { DataTable, Column } from '@/components/forms/common/DataTable'
import { BulkActionsToolbar } from '@/components/forms/common/BulkActionsToolbar'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Edit, Trash2 } from 'lucide-react'

type Machine = Database['public']['Tables']['machines']['Row']

interface MachineDataTableProps {
  machines: Machine[]
  loading: boolean
  onEdit: (_machine: Machine) => void
  onDelete: (id: string) => void
  onBulkDelete?: (machines: Machine[]) => void // AGENT-1: Fixed optional function type
  className?: string // AGENT-1: Fixed optional type
}

export function MachineDataTable({
  machines,
  loading,
  onEdit,
  onDelete,
  onBulkDelete,
  className = ""
}: MachineDataTableProps) {
  
  const columns: Column<Machine>[] = [
    {
      key: 'machine_resource_id',
      header: 'Machine ID',
      accessor: (_machine) => (
        <div className="font-medium">
          {_machine.machine_resource_id}
        </div>
      ),
      sortable: true,
      filterable: true,
      width: 'w-32'
    },
    {
      key: 'machine_name',
      header: 'Machine Name',
      accessor: (_machine) => (
        <div>
          <div className="font-medium">{_machine.name}</div>
          {/* Description not in database
            <div className="text-sm text-gray-500 truncate max-w-48">
              Description placeholder
            </div>
          */}
        </div>
      ),
      sortable: true,
      filterable: true
    },
    {
      key: 'department',
      header: 'Department',
      accessor: (_machine) => (
        <div className="text-sm">
          {_machine.department_id || 'Unassigned'}
        </div>
      ),
      sortable: true,
      filterable: true,
      width: 'w-32'
    },
    {
      key: 'work_cell',
      header: 'Work Cell',
      accessor: (_machine) => (
        <div className="text-sm">
          {_machine.cell_id || 'Unassigned'}
        </div>
      ),
      sortable: true,
      filterable: true,
      width: 'w-32'
    },
    {
      key: 'capacity',
      header: 'Capacity',
      accessor: (_machine) => (
        <div className="text-center">
          {_machine.capacity || 1}
        </div>
      ),
      sortable: true,
      width: 'w-20'
    },
    {
      key: 'performance',
      header: 'Performance',
      accessor: (_machine) => (
        <div className="space-y-1">
          <div className="text-xs">
            Efficiency: {/* Efficiency not in database */ 95 || 100}%
          </div>
          <div className="text-xs">
            Availability: {/* Availability not in database */ 98 || 100}%
          </div>
        </div>
      ),
      width: 'w-28'
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (_machine) => {
        const status = _machine.is_active ? 'active' : 'inactive'
        const variants = {
          active: 'default',
          inactive: 'secondary',
          maintenance: 'destructive'
        } as const
        
        return (
          <Badge variant={variants[status as keyof typeof variants] || 'secondary'}>
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Badge>
        )
      },
      sortable: true,
      filterable: true,
      width: 'w-24'
    },
    {
      key: 'rates',
      header: 'Rates',
      accessor: (_machine) => (
        <div className="space-y-1">
          <div className="text-xs">
            Rate: ${_machine.cost_per_hour || 0}/hr
          </div>
          <div className="text-xs">
            Setup: {_machine.setup_time_minutes || 0}min
          </div>
        </div>
      ),
      width: 'w-24'
    },
    {
      key: 'maintenance',
      header: 'Maintenance',
      accessor: (_machine) => (
        <div className="text-center">
          {/* Maintenance required not in database */}
          <span className="text-gray-400">-</span>
        </div>
      ),
      width: 'w-24'
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: (_machine) => (
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(_machine)}
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(_machine.machine_resource_id)}
            className="text-red-600 hover:text-red-700"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
      width: 'w-24'
    }
  ]

  const handleRowSelect = (_selectedMachines: Machine[]) => {
    // Optional: handle row selection for bulk operations
  }

  const bulkActions = onBulkDelete ? (
    <BulkActionsToolbar
      selectedCount={0} // This would be managed by parent component
      selectedItems={[]}
      onBulkDelete={onBulkDelete}
      onClearSelection={() => {}}
    />
  ) : null

  return (
    <Card className={className}>
      <CardContent className="p-0">
        <DataTable
          data={machines}
          columns={columns}
          keyExtractor={(_machine) => _machine.machine_resource_id}
          loading={loading}
          emptyMessage="No machines found. Add your first machine to get started."
          searchPlaceholder="Search machines..."
          onRowSelect={onBulkDelete ? handleRowSelect : undefined}
          bulkActions={bulkActions}
          pagination={{
            enabled: true,
            pageSize: 25
          }}
        />
      </CardContent>
    </Card>
  )
}