"use client"

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Edit, Trash2, Search, Filter, ArrowUpDown, ChevronUp, ChevronDown } from 'lucide-react'
import { useFormTable, SortConfig } from '@/hooks/forms'

interface Skill {
  skill_id: string
  name: string
  description: string | null
  category: string | null
  department_id: string | null
  department?: { name: string; code: string }
  complexity_level: string
  training_hours_required: number
  certification_required: boolean
  certification_expires_after_months: number | null
  market_hourly_rate: number | null
  skill_scarcity_level: string
  is_active: boolean
  created_at: string
}

interface SkillsTableProps {
  skills: Skill[]
  onEdit: (skill: Skill) => void
  onDelete: (skillId: string) => void
  departments: Array<{ department_id: string; name: string; code: string }>
}

const complexityColors = {
  basic: 'bg-green-100 text-green-800',
  intermediate: 'bg-yellow-100 text-yellow-800',
  advanced: 'bg-orange-100 text-orange-800',
  expert: 'bg-red-100 text-red-800'
}

const scarcityColors = {
  common: 'bg-gray-100 text-gray-800',
  uncommon: 'bg-blue-100 text-blue-800',
  rare: 'bg-purple-100 text-purple-800',
  critical: 'bg-red-100 text-red-800'
}

export function SkillsTable({ skills, onEdit, onDelete, departments }: SkillsTableProps) {
  const {
    data: paginatedSkills,
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
    data: skills,
    itemsPerPage: 10,
    searchableFields: ['name', 'description', 'category'],
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
          <Label htmlFor="search" className="sr-only">Search skills</Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              id="search"
              placeholder="Search skills..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              aria-label="Search skills"
            />
          </div>
        </div>

        <Select
          value={filters.category as string || 'all'}
          onValueChange={(value) => handleFilter('category', value === 'all' ? undefined : value)}
        >
          <SelectTrigger className="w-48" aria-label="Filter by category">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {['mechanical', 'electrical', 'quality', 'assembly', 'testing', 'machining', 'splicing', 'alignment', 'cleaning'].map(cat => (
              <SelectItem key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.complexity_level as string || 'all'}
          onValueChange={(value) => handleFilter('complexity_level', value === 'all' ? undefined : value)}
        >
          <SelectTrigger className="w-48" aria-label="Filter by complexity">
            <SelectValue placeholder="All Complexity" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Complexity</SelectItem>
            <SelectItem value="basic">Basic</SelectItem>
            <SelectItem value="intermediate">Intermediate</SelectItem>
            <SelectItem value="advanced">Advanced</SelectItem>
            <SelectItem value="expert">Expert</SelectItem>
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
                  Name {renderSortIcon('name')}
                </button>
              </th>
              <th className="p-2 text-left">Category</th>
              <th className="p-2 text-left">Department</th>
              <th className="p-2 text-left">
                <button
                  onClick={() => handleSort('complexity_level')}
                  className="flex items-center font-medium hover:text-gray-700"
                  aria-label="Sort by complexity"
                >
                  Complexity {renderSortIcon('complexity_level')}
                </button>
              </th>
              <th className="p-2 text-left">
                <button
                  onClick={() => handleSort('skill_scarcity_level')}
                  className="flex items-center font-medium hover:text-gray-700"
                  aria-label="Sort by scarcity"
                >
                  Scarcity {renderSortIcon('skill_scarcity_level')}
                </button>
              </th>
              <th className="p-2 text-left">Training Hours</th>
              <th className="p-2 text-left">Certification</th>
              <th className="p-2 text-left">Status</th>
              <th className="p-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginatedSkills.map((skill) => {
              const dept = departments.find(d => d.department_id === skill.department_id)
              return (
                <tr key={skill.skill_id} className="border-b hover:bg-gray-50">
                  <td className="p-2">
                    <div>
                      <div className="font-medium">{skill.name}</div>
                      {skill.description && (
                        <div className="text-sm text-gray-500 truncate max-w-xs">
                          {skill.description}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="p-2">
                    {skill.category && (
                      <Badge variant="outline">
                        {skill.category}
                      </Badge>
                    )}
                  </td>
                  <td className="p-2 text-sm">
                    {dept ? `${dept.name} (${dept.code})` : '-'}
                  </td>
                  <td className="p-2">
                    <Badge className={complexityColors[skill.complexity_level as keyof typeof complexityColors]}>
                      {skill.complexity_level}
                    </Badge>
                  </td>
                  <td className="p-2">
                    <Badge className={scarcityColors[skill.skill_scarcity_level as keyof typeof scarcityColors]}>
                      {skill.skill_scarcity_level}
                    </Badge>
                  </td>
                  <td className="p-2 text-sm">{skill.training_hours_required}h</td>
                  <td className="p-2 text-sm">
                    {skill.certification_required ? (
                      <span className="text-green-600">
                        Required
                        {skill.certification_expires_after_months && 
                          ` (${skill.certification_expires_after_months}mo)`
                        }
                      </span>
                    ) : (
                      <span className="text-gray-400">Not required</span>
                    )}
                  </td>
                  <td className="p-2">
                    <Badge variant={skill.is_active ? 'default' : 'secondary'}>
                      {skill.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td className="p-2 text-right">
                    <div className="flex gap-2 justify-end">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onEdit(skill)}
                        aria-label={`Edit ${skill.name}`}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onDelete(skill.skill_id)}
                        aria-label={`Delete ${skill.name}`}
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

// Add missing Label import
import { Label } from '@/components/ui/label'