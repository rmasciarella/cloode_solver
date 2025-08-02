"use client"

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Edit, Trash2, Search, ArrowUpDown, ChevronUp, ChevronDown, Clock, Wrench, Package, Sparkles } from 'lucide-react'
import { useFormTable } from '@/hooks/forms'

interface SetupTime {
  setup_time_id: string
  from_optimized_task_id: string
  to_optimized_task_id: string
  machine_resource_id: string
  setup_time_minutes: number
  notes: string | null
  requires_tool_change: boolean
  requires_material_change: boolean
  requires_cleaning: boolean
  is_sequence_dependent: boolean
  created_at: string
  from_task?: { task_name: string; pattern_name: string }
  to_task?: { task_name: string; pattern_name: string }
  machine?: { name: string; code: string }
}

interface SetupTimesTableProps {
  setupTimes: SetupTime[]
  onEdit: (setupTime: SetupTime) => void
  onDelete: (setupTimeId: string) => void
  optimizedTasks: Array<{ 
    optimized_task_id: string
    task_name: string
    pattern_name: string
  }>
  machines: Array<{ 
    machine_resource_id: string
    name: string
    code: string
  }>
}

export function SetupTimesTable({ 
  setupTimes, 
  onEdit, 
  onDelete,
  optimizedTasks,
  machines 
}: SetupTimesTableProps) {
  const {
    data: paginatedSetupTimes,
    currentPage,
    totalPages,
    setCurrentPage,
    sortConfig,
    handleSort,
    searchTerm,
    setSearchTerm,
    filters,
    handleFilter,
    clearFilters,
    hasFilters
  } = useFormTable({
    data: setupTimes,
    itemsPerPage: 10,
    searchableFields: ['notes'],
    defaultSort: { key: 'setup_time_minutes', direction: 'desc' }
  })

  const renderSortIcon = (key: string) => {
    if (!sortConfig || sortConfig.key !== key) {
      return <ArrowUpDown className="w-4 h-4 ml-1" />
    }
    return sortConfig.direction === 'asc' 
      ? <ChevronUp className="w-4 h-4 ml-1" />
      : <ChevronDown className="w-4 h-4 ml-1" />
  }

  // Create lookup maps for performance
  const taskMap = new Map(optimizedTasks.map(t => [t.optimized_task_id, t]))
  const machineMap = new Map(machines.map(m => [m.machine_resource_id, m]))

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4 items-end">
        <div className="flex-1">
          <Label htmlFor="search" className="sr-only">Search setup times</Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              id="search"
              placeholder="Search notes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              aria-label="Search setup times"
            />
          </div>
        </div>

        <Select
          value={filters.machine_resource_id as string || 'all'}
          onValueChange={(value) => handleFilter('machine_resource_id', value === 'all' ? undefined : value)}
        >
          <SelectTrigger className="w-48" aria-label="Filter by machine">
            <SelectValue placeholder="All Machines" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Machines</SelectItem>
            {machines.map(machine => (
              <SelectItem key={machine.machine_resource_id} value={machine.machine_resource_id}>
                {machine.name} ({machine.code})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.is_sequence_dependent === undefined ? 'all' : filters.is_sequence_dependent.toString()}
          onValueChange={(value) => handleFilter('is_sequence_dependent', value === 'all' ? undefined : value === 'true')}
        >
          <SelectTrigger className="w-48" aria-label="Filter by sequence dependency">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="true">Sequence Dependent</SelectItem>
            <SelectItem value="false">Fixed Duration</SelectItem>
          </SelectContent>
        </Select>

        {hasFilters && (
          <Button variant="ghost" onClick={clearFilters} size="sm">
            Clear Filters
          </Button>
        )}
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="p-2 text-left">From Task</th>
              <th className="p-2 text-left">To Task</th>
              <th className="p-2 text-left">Machine</th>
              <th className="p-2 text-left">
                <button
                  onClick={() => handleSort('setup_time_minutes')}
                  className="flex items-center font-medium hover:text-gray-700"
                  aria-label="Sort by setup time"
                >
                  Setup Time {renderSortIcon('setup_time_minutes')}
                </button>
              </th>
              <th className="p-2 text-left">Requirements</th>
              <th className="p-2 text-left">Type</th>
              <th className="p-2 text-left">Notes</th>
              <th className="p-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginatedSetupTimes.map((setupTime) => {
              const fromTask = taskMap.get(setupTime.from_optimized_task_id)
              const toTask = taskMap.get(setupTime.to_optimized_task_id)
              const machine = machineMap.get(setupTime.machine_resource_id)
              
              return (
                <tr key={setupTime.setup_time_id} className="border-b hover:bg-gray-50">
                  <td className="p-2">
                    <div>
                      <div className="font-medium">{fromTask?.task_name || 'Unknown'}</div>
                      <div className="text-xs text-gray-500">{fromTask?.pattern_name}</div>
                    </div>
                  </td>
                  <td className="p-2">
                    <div>
                      <div className="font-medium">{toTask?.task_name || 'Unknown'}</div>
                      <div className="text-xs text-gray-500">{toTask?.pattern_name}</div>
                    </div>
                  </td>
                  <td className="p-2 text-sm">
                    {machine ? `${machine.name} (${machine.code})` : 'Unknown'}
                  </td>
                  <td className="p-2">
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span className="font-medium">{setupTime.setup_time_minutes} min</span>
                    </div>
                  </td>
                  <td className="p-2">
                    <div className="flex gap-1">
                      {setupTime.requires_tool_change && (
                        <Badge variant="outline" className="text-xs">
                          <Wrench className="w-3 h-3 mr-1" />
                          Tool
                        </Badge>
                      )}
                      {setupTime.requires_material_change && (
                        <Badge variant="outline" className="text-xs">
                          <Package className="w-3 h-3 mr-1" />
                          Material
                        </Badge>
                      )}
                      {setupTime.requires_cleaning && (
                        <Badge variant="outline" className="text-xs">
                          <Sparkles className="w-3 h-3 mr-1" />
                          Clean
                        </Badge>
                      )}
                    </div>
                  </td>
                  <td className="p-2">
                    <Badge variant={setupTime.is_sequence_dependent ? 'default' : 'secondary'}>
                      {setupTime.is_sequence_dependent ? 'Sequence Dependent' : 'Fixed'}
                    </Badge>
                  </td>
                  <td className="p-2">
                    {setupTime.notes && (
                      <div className="text-sm text-gray-500 truncate max-w-xs" title={setupTime.notes}>
                        {setupTime.notes}
                      </div>
                    )}
                  </td>
                  <td className="p-2 text-right">
                    <div className="flex gap-2 justify-end">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onEdit(setupTime)}
                        aria-label={`Edit setup time from ${fromTask?.task_name} to ${toTask?.task_name}`}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onDelete(setupTime.setup_time_id)}
                        aria-label={`Delete setup time from ${fromTask?.task_name} to ${toTask?.task_name}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Page {currentPage} of {totalPages}
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              aria-label="Previous page"
            >
              Previous
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              aria-label="Next page"
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}