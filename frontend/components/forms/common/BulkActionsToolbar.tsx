"use client"

import { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
// Badge component inline implementation
const Badge = ({ variant, className, children }: { 
  variant?: 'secondary' | 'outline' | 'default'
  className?: string
  children: React.ReactNode 
}) => (
  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
    variant === 'secondary' ? 'bg-gray-100 text-gray-800' :
    variant === 'outline' ? 'border border-gray-200 text-gray-700' :
    'bg-blue-100 text-blue-800'
  } ${className || ''}`}>
    {children}
  </span>
)
import { Separator } from '@/components/ui/separator'
import { Edit, Trash2, X, Download, Upload } from 'lucide-react'

interface BulkActionsToolbarProps<T> {
  selectedCount: number
  selectedItems: T[]
  onBulkEdit?: (items: T[]) => void
  onBulkDelete?: (items: T[]) => void
  onBulkExport?: (items: T[]) => void
  onBulkImport?: () => void
  onClearSelection: () => void
  customActions?: ReactNode
  className?: string
}

export function BulkActionsToolbar<T>({
  selectedCount,
  selectedItems,
  onBulkEdit,
  onBulkDelete,
  onBulkExport,
  onBulkImport,
  onClearSelection,
  customActions,
  className = ""
}: BulkActionsToolbarProps<T>) {
  if (selectedCount === 0) {
    return null
  }

  return (
    <div className={`flex items-center gap-4 p-4 bg-gray-50 border-b border-gray-200 ${className}`}>
      <Badge variant="secondary" className="text-sm">
        {selectedCount} item{selectedCount !== 1 ? 's' : ''} selected
      </Badge>
      
      <Separator orientation="vertical" className="h-6" />
      
      <div className="flex items-center gap-2">
        {onBulkEdit && (
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => onBulkEdit(selectedItems)}
            disabled={selectedCount === 0}
          >
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </Button>
        )}
        
        {onBulkDelete && (
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => onBulkDelete(selectedItems)}
            disabled={selectedCount === 0}
            className="text-red-600 hover:text-red-700"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        )}
        
        {onBulkExport && (
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => onBulkExport(selectedItems)}
            disabled={selectedCount === 0}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        )}
        
        {onBulkImport && (
          <Button 
            variant="outline" 
            size="sm"
            onClick={onBulkImport}
          >
            <Upload className="h-4 w-4 mr-2" />
            Import
          </Button>
        )}
        
        {customActions}
      </div>
      
      <div className="ml-auto">
        <Button 
          variant="ghost" 
          size="sm"
          onClick={onClearSelection}
          className="text-gray-500 hover:text-gray-700"
        >
          <X className="h-4 w-4 mr-2" />
          Clear Selection
        </Button>
      </div>
    </div>
  )
}