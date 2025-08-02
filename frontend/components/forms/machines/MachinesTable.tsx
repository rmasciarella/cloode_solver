"use client"

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Edit, Trash2, Search, ArrowUpDown, ChevronUp, ChevronDown } from 'lucide-react'
import { useFormTable } from '@/hooks/forms'

interface Machine {
  machine_resource_id: string
  name: string
  code: string
  description: string | null
  machine_type: string
  department_id: string | null
  department?: { name: string; code: string }
  capacity_per_hour: number
  setup_time_minutes: number
  maintenance_interval_hours: number
  hourly_operating_cost: number
  is_active: boolean
  requires_skilled_operator: boolean
  created_at: string
}

interface MachinesTableProps {
  machines: Machine[]
  onEdit: (machine: Machine) => void
  onDelete: (machineId: string) => void
  departments: Array<{ department_id: string; name: string; code: string }>
}

const machineTypeLabels: Record<string, string> = {
  cnc: 'CNC Machine',
  laser: 'Laser Cutter',
  welding: 'Welding Station',
  assembly: 'Assembly Line',
  packaging: 'Packaging Machine',
  testing: 'Testing Equipment',
  other: 'Other'
}

export function MachinesTable({ machines, onEdit, onDelete, departments }: MachinesTableProps) {
  const {
    data: paginatedMachines,
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
    data: machines,
    itemsPerPage: 10,
    searchableFields: ['name', 'code', 'description'],
    defaultSort: { key: 'name', direction: 'asc' }
  })

  const renderSortIcon = (key: string) => {
    if (!sortConfig || sortConfig.key !== key) {
      return <ArrowUpDown className="w-4 h-4 ml-1" />
    }
    return sortConfig.direction === 'asc' 
      ? <ChevronUp className="w-4 h-4 ml-1" />
      : <ChevronDown className="w-4 h-4 ml-1" />
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4 items-end">
        <div className="flex-1">
          <Label htmlFor="search" className="sr-only">Search machines</Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              id="search"
              placeholder="Search machines..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              aria-label="Search machines"
            />
          </div>
        </div>

        <Select
          value={filters.machine_type as string || 'all'}
          onValueChange={(value) => handleFilter('machine_type', value === 'all' ? undefined : value)}
        >
          <SelectTrigger className="w-48" aria-label="Filter by machine type">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {Object.entries(machineTypeLabels).map(([value, label]) => (
              <SelectItem key={value} value={value}>{label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.department_id as string || 'all'}
          onValueChange={(value) => handleFilter('department_id', value === 'all' ? undefined : value)}
        >
          <SelectTrigger className="w-48" aria-label="Filter by department">
            <SelectValue placeholder="All Departments" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Departments</SelectItem>
            {departments.map(dept => (
              <SelectItem key={dept.department_id} value={dept.department_id}>
                {dept.name} ({dept.code})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.is_active === undefined ? 'all' : filters.is_active.toString()}
          onValueChange={(value) => handleFilter('is_active', value === 'all' ? undefined : value === 'true')}
        >
          <SelectTrigger className="w-32" aria-label="Filter by status">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="true">Active</SelectItem>
            <SelectItem value="false">Inactive</SelectItem>
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
              <th className="p-2 text-left">
                <button
                  onClick={() => handleSort('name')}
                  className="flex items-center font-medium hover:text-gray-700"
                  aria-label="Sort by name"
                >
                  Machine {renderSortIcon('name')}
                </button>
              </th>
              <th className="p-2 text-left">
                <button
                  onClick={() => handleSort('machine_type')}
                  className="flex items-center font-medium hover:text-gray-700"
                  aria-label="Sort by type"
                >
                  Type {renderSortIcon('machine_type')}
                </button>
              </th>
              <th className="p-2 text-left">Department</th>
              <th className="p-2 text-left">
                <button
                  onClick={() => handleSort('capacity_per_hour')}
                  className="flex items-center font-medium hover:text-gray-700"
                  aria-label="Sort by capacity"
                >
                  Capacity/Hour {renderSortIcon('capacity_per_hour')}
                </button>
              </th>
              <th className="p-2 text-left">Setup Time</th>
              <th className="p-2 text-left">
                <button
                  onClick={() => handleSort('hourly_operating_cost')}
                  className="flex items-center font-medium hover:text-gray-700"
                  aria-label="Sort by cost"
                >
                  Cost/Hour {renderSortIcon('hourly_operating_cost')}
                </button>
              </th>
              <th className="p-2 text-left">Features</th>
              <th className="p-2 text-left">Status</th>
              <th className="p-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginatedMachines.map((machine) => {
              const dept = departments.find(d => d.department_id === machine.department_id)
              return (
                <tr key={machine.machine_resource_id} className="border-b hover:bg-gray-50">
                  <td className="p-2">
                    <div>
                      <div className="font-medium">{machine.name}</div>
                      <div className="text-sm text-gray-500">{machine.code}</div>
                      {machine.description && (
                        <div className="text-sm text-gray-400 truncate max-w-xs">
                          {machine.description}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="p-2">
                    <Badge variant="outline">
                      {machineTypeLabels[machine.machine_type] || machine.machine_type}
                    </Badge>
                  </td>
                  <td className="p-2 text-sm">
                    {dept ? `${dept.name} (${dept.code})` : '-'}
                  </td>
                  <td className="p-2 text-sm">{machine.capacity_per_hour} units</td>
                  <td className="p-2 text-sm">{machine.setup_time_minutes} min</td>
                  <td className="p-2 text-sm">${machine.hourly_operating_cost.toFixed(2)}</td>
                  <td className="p-2">
                    <div className="flex gap-1">
                      {machine.requires_skilled_operator && (
                        <Badge variant="secondary" className="text-xs">
                          Skilled Op
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-xs">
                        {machine.maintenance_interval_hours}h maint
                      </Badge>
                    </div>
                  </td>
                  <td className="p-2">
                    <Badge variant={machine.is_active ? 'default' : 'secondary'}>
                      {machine.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td className="p-2 text-right">
                    <div className="flex gap-2 justify-end">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onEdit(machine)}
                        aria-label={`Edit ${machine.name}`}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onDelete(machine.machine_resource_id)}
                        aria-label={`Delete ${machine.name}`}
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