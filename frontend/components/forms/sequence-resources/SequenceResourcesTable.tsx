"use client"

import { Database } from '@/lib/database.types'
import { Button } from '@/components/ui/button'
import { Loader2, Edit, Trash2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AdvancedFilter, BulkOperations, useAdvancedTable } from '@/components/ui/advanced-patterns'

interface SequenceResourcesTableProps {
  sequenceResources: Database['public']['Tables']['sequence_resources']['Row'][]
  departments: Database['public']['Tables']['departments']['Row'][]
  onEdit: (resource: Database['public']['Tables']['sequence_resources']['Row']) => void
  onDelete: (id: string, name: string) => void
  onToggleActive: (id: string, name: string, isActive: boolean) => void
  loading: boolean
}

export function SequenceResourcesTable({
  sequenceResources,
  departments,
  onEdit,
  onDelete,
  onToggleActive,
  loading
}: SequenceResourcesTableProps) {
  const advancedTable = useAdvancedTable(
    sequenceResources,
    (resource) => resource.sequence_id,
    {
      enableFiltering: true,
      enableBulkOperations: true,
      enableSorting: true
    }
  )

  const filterOptions = [
    { key: 'name', label: 'Name', type: 'text' as const },
    { key: 'resource_type', label: 'Resource Type', type: 'text' as const },
    { key: 'department_id', label: 'Department', type: 'text' as const },
    { key: 'is_active', label: 'Active', type: 'boolean' as const }
  ]

  return (
    <Card id="sequence-resource-list">
      <CardHeader>
        <CardTitle>Sequence Resources ({advancedTable.filteredCount} of {advancedTable.totalCount})</CardTitle>
        <CardDescription>Manage existing sequence resources with advanced filtering and bulk operations</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Advanced Filter */}
        <AdvancedFilter
          options={filterOptions}
          values={advancedTable.filters}
          onChange={advancedTable.setFilters}
          placeholder="Search sequence resources..."
        />

        {/* Bulk Operations */}
        <BulkOperations
          items={advancedTable.filteredItems}
          selectedItems={advancedTable.selectedItems}
          onToggleSelection={advancedTable.toggleSelection}
          onSelectAll={advancedTable.selectAll}
          onClearSelection={advancedTable.clearSelection}
          onBulkDelete={() => onDelete && Array.from(advancedTable.selectedItems).forEach(id => {
            const resource = sequenceResources.find(r => r.sequence_id === id)
            if (resource) {
              onDelete(id, resource.name)
            }
          })}
          onBulkEdit={() => Array.from(advancedTable.selectedItems).forEach(id => {
            const resource = sequenceResources.find(r => r.sequence_id === id)
            if (resource) {
              onToggleActive(id, resource.name, resource.is_active)
            }
          })}
          getId={(resource) => resource.sequence_id}
          isSelectionMode={advancedTable.isSelectionMode}
          onEnterSelectionMode={advancedTable.enterSelectionMode}
        />

        {loading ? (
          <div className="flex justify-center py-4">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : advancedTable.isEmpty ? (
          <p className="text-center text-gray-500 py-4">
            {advancedTable.filters.length > 0 ? 'No sequence resources match your filters' : 'No sequence resources found'}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse table-fixed">
              <thead>
                <tr className="border-b">
                  {advancedTable.isSelectionMode && (
                    <th className="text-left p-2 w-12">
                      <input
                        type="checkbox"
                        checked={advancedTable.selectedItems.size === advancedTable.filteredItems.length}
                        onChange={() => {
                          advancedTable.selectedItems.size === advancedTable.filteredItems.length ? advancedTable.clearSelection() : advancedTable.selectAll()
                        }}
                        className="rounded"
                      />
                    </th>
                  )}
                  <th className="text-left p-2 font-medium cursor-pointer hover:bg-gray-50" onClick={() => advancedTable.setSortBy('name')}>Name ↕</th>
                  <th className="text-left p-2 font-medium">Resource Type</th>
                  <th className="text-left p-2 font-medium">Department</th>
                  <th className="text-left p-2 font-medium">Max Jobs</th>
                  <th className="text-left p-2 font-medium">Priority</th>
                  <th className="text-left p-2 font-medium">Status</th>
                  <th className="text-left p-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {advancedTable.filteredItems.map((resource) => {
                  const department = departments.find(d => d.department_id === resource.department_id)
                  return (
                    <tr key={resource.sequence_id} className="border-b hover:bg-gray-50">
                      {advancedTable.isSelectionMode && (
                        <td className="p-2">
                          <input
                            type="checkbox"
                            checked={advancedTable.selectedItems.has(resource.sequence_id)}
                            onChange={() => advancedTable.toggleSelection(resource.sequence_id)}
                            className="rounded"
                          />
                        </td>
                      )}
                      <td className="p-2 font-medium">{resource.name}</td>
                      <td className="p-2">{resource.resource_type}</td>
                      <td className="p-2">{department ? department.name : '-'}</td>
                      <td className="p-2">{resource.max_concurrent_jobs}</td>
                      <td className="p-2">{resource.priority}</td>
                      <td className="p-2">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          resource.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {resource.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="p-2">
                        <div className="flex space-x-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onEdit(resource)}
                            disabled={loading}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onToggleActive(resource.sequence_id, resource.name, resource.is_active)}
                            className={resource.is_active ? "text-orange-600 hover:bg-orange-50" : "text-green-600 hover:bg-green-50"}
                            disabled={loading}
                          >
                            {resource.is_active ? "Deactivate" : "Reactivate"}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onDelete(resource.sequence_id, resource.name)}
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
