"use client"

import { Database } from '@/lib/database.types'
import { Button } from '@/components/ui/button'
import { Edit, Trash2 } from 'lucide-react'
import { getTimeRangeDescription } from '@/lib/timeUtils'

type Department = Database['public']['Tables']['departments']['Row']

interface DepartmentsTableProps {
  departments: Department[]
  onEdit: (department: Department) => void
  onDelete: (id: string, name: string) => void
  onToggleActive: (id: string, name: string, isActive: boolean) => void
  loading?: boolean
  selectedItems?: Set<string>
  onToggleSelection?: (id: string) => void
  isSelectionMode?: boolean
  onSort?: (column: string) => void
}

export function DepartmentsTable({
  departments,
  onEdit,
  onDelete,
  onToggleActive,
  loading = false,
  selectedItems = new Set(),
  onToggleSelection,
  isSelectionMode = false,
  onSort
}: DepartmentsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b">
            {isSelectionMode && (
              <th className="text-left p-2 w-12">
                <input
                  type="checkbox"
                  checked={selectedItems.size === departments.length && departments.length > 0}
                  onChange={() => {
                    if (selectedItems.size === departments.length) {
                      departments.forEach(dept => onToggleSelection?.(dept.department_id))
                    } else {
                      departments.forEach(dept => {
                        if (!selectedItems.has(dept.department_id)) {
                          onToggleSelection?.(dept.department_id)
                        }
                      })
                    }
                  }}
                  className="rounded"
                  aria-label="Select all departments"
                />
              </th>
            )}
            <th 
              className="text-left p-2 font-medium cursor-pointer hover:bg-gray-50" 
              onClick={() => onSort?.('code')}
              role="button"
              tabIndex={0}
              aria-label="Sort by code"
            >
              Code ↕
            </th>
            <th 
              className="text-left p-2 font-medium cursor-pointer hover:bg-gray-50" 
              onClick={() => onSort?.('name')}
              role="button"
              tabIndex={0}
              aria-label="Sort by name"
            >
              Name ↕
            </th>
            <th className="text-left p-2 font-medium">Cost Center</th>
            <th className="text-left p-2 font-medium">Shift Times</th>
            <th className="text-left p-2 font-medium">Status</th>
            <th className="text-left p-2 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {departments.map((department) => (
            <tr key={department.department_id} className="border-b hover:bg-gray-50">
              {isSelectionMode && (
                <td className="p-2">
                  <input
                    type="checkbox"
                    checked={selectedItems.has(department.department_id)}
                    onChange={() => onToggleSelection?.(department.department_id)}
                    className="rounded"
                    aria-label={`Select ${department.name}`}
                  />
                </td>
              )}
              <td className="p-2 font-medium">{department.code}</td>
              <td className="p-2">{department.name}</td>
              <td className="p-2">{department.cost_center || '-'}</td>
              <td className="p-2">
                {getTimeRangeDescription(department.default_shift_start, department.default_shift_end)}
              </td>
              <td className="p-2">
                <span className={`px-2 py-1 rounded-full text-xs ${
                  department.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {department.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td className="p-2">
                <div className="flex space-x-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onEdit(department)}
                    disabled={loading}
                    aria-label={`Edit ${department.name}`}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onToggleActive(department.department_id, department.name, department.is_active)}
                    className={department.is_active ? "text-orange-600 hover:bg-orange-50" : "text-green-600 hover:bg-green-50"}
                    disabled={loading}
                    aria-label={department.is_active ? `Deactivate ${department.name}` : `Reactivate ${department.name}`}
                  >
                    {department.is_active ? "Deactivate" : "Reactivate"}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onDelete(department.department_id, department.name)}
                    className="text-red-600 hover:bg-red-50"
                    disabled={loading}
                    aria-label={`Delete ${department.name}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}