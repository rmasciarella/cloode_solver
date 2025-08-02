"use client"

import { ReactNode, useState, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
// import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
// import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Search, ChevronUp, ChevronDown, SortAsc } from 'lucide-react'

export interface Column<T> {
  key: string
  header: string
  accessor: (item: T) => ReactNode
  sortable?: boolean
  filterable?: boolean
  width?: string
}

interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  searchPlaceholder?: string
  onRowSelect?: (selectedItems: T[]) => void
  bulkActions?: ReactNode
  keyExtractor: (item: T) => string
  loading?: boolean
  emptyMessage?: string
  pagination?: {
    enabled: boolean
    pageSize?: number
  }
  className?: string
}

export function DataTable<T>({
  data,
  columns,
  searchPlaceholder = "Search...",
  onRowSelect,
  bulkActions,
  keyExtractor,
  loading = false,
  emptyMessage = "No data available",
  pagination = { enabled: true, pageSize: 50 },
  className = ""
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState("")
  const [sortConfig, setSortConfig] = useState<{
    key: string
    direction: 'asc' | 'desc'
  } | null>(null)
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())
  const [currentPage, setCurrentPage] = useState(1)

  // Filter and sort data
  const processedData = useMemo(() => {
    let filtered = data

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(item => {
        return columns.some(column => {
          if (!column.filterable) return false
          const value = column.accessor(item)
          return String(value).toLowerCase().includes(searchTerm.toLowerCase())
        })
      })
    }

    // Apply sorting
    if (sortConfig) {
      filtered = [...filtered].sort((a, b) => {
        const column = columns.find(col => col.key === sortConfig.key)
        if (!column) return 0

        const aValue = String(column.accessor(a))
        const bValue = String(column.accessor(b))

        if (sortConfig.direction === 'asc') {
          return aValue.localeCompare(bValue)
        } else {
          return bValue.localeCompare(aValue)
        }
      })
    }

    return filtered
  }, [data, searchTerm, sortConfig, columns])

  // Apply pagination
  const paginatedData = useMemo(() => {
    if (!pagination.enabled) return processedData
    
    const startIndex = (currentPage - 1) * (pagination.pageSize || 50)
    const endIndex = startIndex + (pagination.pageSize || 50)
    return processedData.slice(startIndex, endIndex)
  }, [processedData, currentPage, pagination])

  const totalPages = pagination.enabled 
    ? Math.ceil(processedData.length / (pagination.pageSize || 50))
    : 1

  const handleSort = (columnKey: string) => {
    const column = columns.find(col => col.key === columnKey)
    if (!column?.sortable) return

    setSortConfig(current => {
      if (current?.key === columnKey) {
        return current.direction === 'asc' 
          ? { key: columnKey, direction: 'desc' }
          : null
      }
      return { key: columnKey, direction: 'asc' }
    })
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allKeys = new Set(paginatedData.map(keyExtractor))
      setSelectedItems(allKeys)
      onRowSelect?.(paginatedData)
    } else {
      setSelectedItems(new Set())
      onRowSelect?.([])
    }
  }

  const handleSelectItem = (item: T, checked: boolean) => {
    const key = keyExtractor(item)
    const newSelected = new Set(selectedItems)
    
    if (checked) {
      newSelected.add(key)
    } else {
      newSelected.delete(key)
    }
    
    setSelectedItems(newSelected)
    
    const selectedData = data.filter(dataItem => 
      newSelected.has(keyExtractor(dataItem))
    )
    onRowSelect?.(selectedData)
  }

  const isAllSelected = paginatedData.length > 0 && 
    paginatedData.every(item => selectedItems.has(keyExtractor(item)))

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Search and filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder={searchPlaceholder}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        
        {selectedItems.size > 0 && (
          <div className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
            {selectedItems.size} selected
          </div>
        )}
      </div>

      {/* Bulk actions */}
      {bulkActions && selectedItems.size > 0 && (
        <div className="border-b pb-4">
          {bulkActions}
        </div>
      )}

      {/* Table */}
      <div className="border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                {onRowSelect && (
                  <th className="px-4 py-3 text-left w-12">
                    <Checkbox
                      checked={isAllSelected}
                      onCheckedChange={handleSelectAll}
                      aria-label="Select all items"
                    />
                  </th>
                )}
                {columns.map((column) => (
                  <th
                    key={column.key}
                    className={`px-4 py-3 text-left font-medium text-gray-900 ${
                      column.width || ''
                    }`}
                  >
                    {column.sortable ? (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleSort(column.key)}
                        className="h-auto p-0 font-medium text-gray-900 hover:text-gray-700"
                      >
                        {column.header}
                        {sortConfig?.key === column.key ? (
                          sortConfig.direction === 'asc' ? (
                            <ChevronUp className="ml-1 h-4 w-4" />
                          ) : (
                            <ChevronDown className="ml-1 h-4 w-4" />
                          )
                        ) : (
                          <SortAsc className="ml-1 h-4 w-4 opacity-50" />
                        )}
                      </Button>
                    ) : (
                      column.header
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td 
                    colSpan={columns.length + (onRowSelect ? 1 : 0)} 
                    className="px-4 py-8 text-center text-gray-500"
                  >
                    Loading...
                  </td>
                </tr>
              ) : paginatedData.length === 0 ? (
                <tr>
                  <td 
                    colSpan={columns.length + (onRowSelect ? 1 : 0)} 
                    className="px-4 py-8 text-center text-gray-500"
                  >
                    {emptyMessage}
                  </td>
                </tr>
              ) : (
                paginatedData.map((item) => {
                  const key = keyExtractor(item)
                  const isSelected = selectedItems.has(key)
                  
                  return (
                    <tr 
                      key={key}
                      className={`hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}
                    >
                      {onRowSelect && (
                        <td className="px-4 py-3">
                          <Checkbox
                            checked={isSelected}
                            onCheckedChange={(checked) => 
                              handleSelectItem(item, checked === true)
                            }
                            aria-label={`Select item ${key}`}
                          />
                        </td>
                      )}
                      {columns.map((column) => (
                        <td key={column.key} className="px-4 py-3">
                          {column.accessor(item)}
                        </td>
                      ))}
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {pagination.enabled && totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {(currentPage - 1) * (pagination.pageSize || 50) + 1} to{' '}
            {Math.min(currentPage * (pagination.pageSize || 50), processedData.length)} of{' '}
            {processedData.length} results
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              Previous
            </Button>
            
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const page = i + 1
                return (
                  <Button
                    key={page}
                    variant={currentPage === page ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCurrentPage(page)}
                  >
                    {page}
                  </Button>
                )
              })}
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}