"use client"

import { Database } from '@/lib/database.types'
import { Button } from '@/components/ui/button'
import { Loader2, Edit, Trash2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AdvancedFilter, BulkOperations, useAdvancedTable } from '@/components/ui/advanced-patterns'

interface WorkCellsTableProps {
  workCells: Database['public']['Tables']['work_cells']['Row'][]
  departments: Database['public']['Tables']['departments']['Row'][]
  onEdit: (workCell: Database['public']['Tables']['work_cells']['Row']) => void
  onDelete: (id: string) => void
  onBulkDelete: (ids: string[]) => void
  onBulkToggleActive: (ids: string[]) => void
  loading: boolean
}

export function WorkCellsTable({
  workCells,
  departments,
  onEdit,
  onDelete,
  onBulkDelete,
  onBulkToggleActive,
  loading
}: WorkCellsTableProps) {
  const advancedTable = useAdvancedTable(
    workCells,
    (workCell) => workCell.cell_id,
    {
      enableFiltering: true,
      enableBulkOperations: true,
      enableSorting: true
    }
  )

  const filterOptions = [
    { key: 'name', label: 'Name', type: 'text' as const },
    { key: 'cell_type', label: 'Cell Type', type: 'text' as const },
    { key: 'department_id', label: 'Department', type: 'text' as const },
    { key: 'is_active', label: 'Active', type: 'boolean' as const }
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Work Cells ({advancedTable.filteredCount} of {advancedTable.totalCount})</CardTitle>
        <CardDescription>Manage existing work cells with advanced filtering and bulk operations</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Advanced Filter */}
        <AdvancedFilter
          options={filterOptions}
          values={advancedTable.filters}
          onChange={advancedTable.setFilters}
          placeholder="Search work cells..."
        />

        {/* Bulk Operations */}
        <BulkOperations
          items={advancedTable.filteredItems}
          selectedItems={advancedTable.selectedItems}
          onToggleSelection={advancedTable.toggleSelection}
          onSelectAll={() => advancedTable.selectAll(advancedTable.filteredItems, (cell) => cell.cell_id)}
          onClearSelection={advancedTable.clearSelection}
          onBulkDelete={() => onBulkDelete(Array.from(advancedTable.selectedItems))}
          onBulkEdit={() => onBulkToggleActive(Array.from(advancedTable.selectedItems))}
          getId={(workCell) => workCell.cell_id}
          isSelectionMode={advancedTable.isSelectionMode}
          onEnterSelectionMode={advancedTable.enterSelectionMode}
        />

        {loading ? (
          <div className="flex justify-center py-4">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : advancedTable.isEmpty ? (
          <p className="text-center text-gray-500 py-4">
            {advancedTable.filters.length > 0 ? 'No work cells match your filters' : 'No work cells found'}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  {advancedTable.isSelectionMode && (
                    <th className="text-left p-2 w-12">
                      <input
                        type="checkbox"
                        checked={advancedTable.selectedItems.size === advancedTable.filteredItems.length}
                        onChange={() => {
                          if (advancedTable.selectedItems.size === advancedTable.filteredItems.length) {
                            advancedTable.clearSelection()
                          } else {
                            advancedTable.selectAll(advancedTable.filteredItems, (cell) => cell.cell_id)
                          }
                        }}
                        className="rounded"
                      />
                    </th>
                  )}
                  <th className="text-left p-2 font-medium cursor-pointer hover:bg-gray-50" onClick={() => advancedTable.setSortBy('name')}>Name ↕</th>
                  <th className="text-left p-2 font-medium">Cell Type</th>
                  <th className="text-left p-2 font-medium">Department</th>
                  <th className="text-left p-2 font-medium">Capacity</th>
                  <th className="text-left p-2 font-medium">WIP Limit</th>
                  <th className="text-left p-2 font-medium">Target Util.</th>
                  <th className="text-left p-2 font-medium">Priority</th>
                  <th className="text-left p-2 font-medium">Status</th>
                  <th className="text-left p-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {advancedTable.filteredItems.map((cell) => {
                  const department = departments.find(d => d.department_id === cell.department_id)
                  return (
                    <tr key={cell.cell_id} className="border-b hover:bg-gray-50">
                      {advancedTable.isSelectionMode && (
                        <td className="p-2">
                          <input
                            type="checkbox"
                            checked={advancedTable.selectedItems.has(cell.cell_id)}
                            onChange={() => advancedTable.toggleSelection(cell.cell_id)}
                            className="rounded"
                          />
                        </td>
                      )}
                      <td className="p-2 font-medium">
                        <div>
                          {cell.name}
                          {cell.floor_location && (
                            <div className="text-xs text-gray-500">{cell.floor_location}</div>
                          )}
                        </div>
                      </td>
                      <td className="p-2 capitalize">{cell.cell_type}</td>
                      <td className="p-2">{department ? `${department.name} (${department.code})` : '-'}</td>
                      <td className="p-2">{cell.capacity}</td>
                      <td className="p-2">{cell.wip_limit || '-'}</td>
                      <td className="p-2">{(cell.target_utilization * 100).toFixed(1)}%</td>
                      <td className="p-2">{cell.flow_priority}</td>
                      <td className="p-2">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          cell.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {cell.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="p-2">
                        <div className="flex space-x-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onEdit(cell)}
                            disabled={loading}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onBulkToggleActive([cell.cell_id])}
                            className={cell.is_active ? "text-orange-600 hover:bg-orange-50" : "text-green-600 hover:bg-green-50"}
                            disabled={loading}
                          >
                            {cell.is_active ? "Deactivate" : "Reactivate"}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onDelete(cell.cell_id)}
                            className="text-red-600 hover:bg-red-50"
                            disabled={loading}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
