"use client"

import { Database } from '@/lib/database.types'
import { Button } from '@/components/ui/button'
import { Edit, Trash2 } from 'lucide-react'

type JobTemplate = Database['public']['Tables']['job_optimized_patterns']['Row']

interface JobTemplatesTableProps {
  jobTemplates: JobTemplate[]
  onEdit: (template: JobTemplate) => void
  onDelete: (id: string, name: string) => void
  onToggleActive: (id: string, name: string, isActive: boolean) => void
  loading?: boolean
  selectedItems?: Set<string>
  onToggleSelection?: (id: string) => void
  isSelectionMode?: boolean
  onSort?: (column: string) => void
  trackInteraction?: (type: string, action: string) => void
}

export function JobTemplatesTable({
  jobTemplates,
  onEdit,
  onDelete,
  onToggleActive,
  loading = false,
  selectedItems = new Set(),
  onToggleSelection,
  isSelectionMode = false,
  onSort,
  trackInteraction
}: JobTemplatesTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b">
            {isSelectionMode && (
              <th className="text-left p-2 w-12">
                <input
                  type="checkbox"
                  checked={selectedItems.size === jobTemplates.length && jobTemplates.length > 0}
                  onChange={() => {
                    trackInteraction?.('click', 'select_all_toggle')
                    if (selectedItems.size === jobTemplates.length) {
                      jobTemplates.forEach(template => onToggleSelection?.(template.pattern_id))
                    } else {
                      jobTemplates.forEach(template => {
                        if (!selectedItems.has(template.pattern_id)) {
                          onToggleSelection?.(template.pattern_id)
                        }
                      })
                    }
                  }}
                  className="rounded"
                  aria-label="Select all job templates"
                />
              </th>
            )}
            <th 
              className="text-left p-2 font-medium cursor-pointer hover:bg-gray-50" 
              onClick={() => {
                trackInteraction?.('click', 'sort_by_name')
                onSort?.('name')
              }}
              role="button"
              tabIndex={0}
              aria-label="Sort by name"
            >
              Name ↕
            </th>
            <th className="text-left p-2 font-medium">Task Count</th>
            <th className="text-left p-2 font-medium">Description</th>
            <th className="text-left p-2 font-medium">Status</th>
            <th className="text-left p-2 font-medium">Created</th>
            <th className="text-left p-2 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobTemplates.map((template) => (
            <tr key={template.pattern_id} className="border-b hover:bg-gray-50">
              {isSelectionMode && (
                <td className="p-2">
                  <input
                    type="checkbox"
                    checked={selectedItems.has(template.pattern_id)}
                    onChange={() => {
                      trackInteraction?.('click', 'row_select')
                      onToggleSelection?.(template.pattern_id)
                    }}
                    className="rounded"
                    aria-label={`Select ${template.name}`}
                  />
                </td>
              )}
              <td className="p-2 font-medium">
                <div>
                  {template.name}
                  {template.description && (
                    <div className="text-xs text-gray-500 truncate max-w-xs">{template.description}</div>
                  )}
                </div>
              </td>
              <td className="p-2">{template.task_count}</td>
              <td className="p-2">{template.description || '-'}</td>
              <td className="p-2">
                <span className={`px-2 py-1 rounded-full text-xs ${
                  template.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {template.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td className="p-2">
                {new Date(template.created_at).toLocaleDateString()}
              </td>
              <td className="p-2">
                <div className="flex space-x-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      trackInteraction?.('click', 'edit_button')
                      onEdit(template)
                    }}
                    disabled={loading}
                    aria-label={`Edit ${template.name}`}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      trackInteraction?.('click', 'toggle_active_button')
                      onToggleActive(template.pattern_id, template.name, template.is_active)
                    }}
                    className={template.is_active ? "text-orange-600 hover:bg-orange-50" : "text-green-600 hover:bg-green-50"}
                    disabled={loading}
                    aria-label={template.is_active ? `Deactivate ${template.name}` : `Activate ${template.name}`}
                  >
                    {template.is_active ? "Deactivate" : "Reactivate"}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      trackInteraction?.('click', 'delete_button')
                      onDelete(template.pattern_id, template.name)
                    }}
                    className="text-red-600 hover:bg-red-50"
                    disabled={loading}
                    aria-label={`Delete ${template.name}`}
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