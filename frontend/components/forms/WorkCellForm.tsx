"use client"

import { useState, useEffect, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { workCellService, departmentService } from '@/lib/services'
import { workCellFormSchema, type WorkCellFormData, cellTypes } from '@/lib/schemas'
import { Database } from '@/lib/database.types'
import { useToast } from '@/hooks/use-toast'
// Performance monitoring removed to fix console errors
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MassUploader } from '@/components/ui/mass-uploader'
import { Loader2, Edit, Trash2, Upload, Search, Filter } from 'lucide-react'
import { AdvancedFilter, BulkOperations, useAdvancedTable } from '@/components/ui/advanced-patterns'

type WorkCell = Database['public']['Tables']['work_cells']['Row']
type Department = Database['public']['Tables']['departments']['Row']

export default function WorkCellForm() {
  const [workCells, setWorkCells] = useState<WorkCell[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showPerformanceDashboard, setShowPerformanceDashboard] = useState(false)
  const { toast } = useToast()
  // Performance monitoring removed

  // Advanced table functionality
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

  // Performance monitoring for field validation
  const validateField = useCallback((fieldName: string, value: any) => {
    const startTime = performance.now()
    let isValid = true
    let error = ''

    try {
      switch (fieldName) {
        case 'name':
          isValid = typeof value === 'string' && value.trim().length > 0
          error = isValid ? '' : 'Work cell name is required'
          break
        case 'capacity':
          isValid = Number.isInteger(value) && value >= 1
          error = isValid ? '' : 'Capacity must be at least 1'
          break
        case 'wip_limit':
          isValid = Number.isInteger(value) && value >= 0
          error = isValid ? '' : 'WIP limit must be non-negative'
          break
        case 'target_utilization':
          isValid = typeof value === 'number' && value >= 0 && value <= 100
          error = isValid ? '' : 'Target utilization must be between 0 and 100%'
          break
        case 'flow_priority':
          isValid = Number.isInteger(value) && value >= 1
          error = isValid ? '' : 'Flow priority must be at least 1'
          break
        case 'average_throughput_per_hour':
          isValid = typeof value === 'number' && value >= 0
          error = isValid ? '' : 'Throughput must be non-negative'
          break
        case 'cell_type':
          isValid = cellTypes.includes(value)
          error = isValid ? '' : 'Invalid cell type'
          break
        default:
          isValid = true
      }
    } catch (err) {
      isValid = false
      error = String(err)
    }

    return { isValid, error }
  }, [])

  // Bulk operations handlers
  const handleBulkDelete = async (ids: string[]) => {
    for (const id of ids) {
      const response = await workCellService.delete(id)
      if (!response.success) {
        toast({
          title: "Error",
          description: `Failed to delete work cell: ${response.error}`,
          variant: "destructive"
        })
        return
      }
    }
    toast({
      title: "Success", 
      description: `Successfully deleted ${ids.length} work cells`
    })
    fetchWorkCells()
    advancedTable.clearSelection()
  }

  const handleBulkToggleActive = async (ids: string[]) => {
    for (const id of ids) {
      const workCell = workCells.find(c => c.cell_id === id)
      if (workCell) {
        const response = await workCellService.update(id, { is_active: !workCell.is_active })
        if (!response.success) {
          toast({
            title: "Error",
            description: `Failed to update work cell: ${response.error}`,
            variant: "destructive"
          })
          return
        }
      }
    }
    toast({
      title: "Success",
      description: `Successfully updated ${ids.length} work cells`
    })
    fetchWorkCells()
    advancedTable.clearSelection()
  }

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<WorkCellFormData>({
    resolver: zodResolver(workCellFormSchema),
    defaultValues: {
      name: '',
      capacity: 1,
      department_id: '',
      wip_limit: 5,
      flow_priority: 1,
      floor_location: '',
      cell_type: 'production',
      target_utilization: 85,  // Form input expects percentage (0-100)
      calendar_id: '',
      average_throughput_per_hour: 0,
      is_active: true
    }
  })

  const fetchWorkCells = async () => {
    setLoading(true)
    
    try {
      const response = await workCellService.getAll()
      
      if (response.success && response.data) {
        setWorkCells(response.data)
      } else {
        const errorMsg = response.error || "Failed to fetch work cells"
        console.error('Error fetching work cells:', response.error)
        
        toast({
          title: "Error",
          description: errorMsg,
          variant: "destructive"
        })
      }
    } catch (error) {
      const errorMsg = String(error)
      
      toast({
        title: "Error",
        description: "Failed to fetch work cells",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchDepartments = async () => {
    try {
      const response = await departmentService.getAll(true) // activeOnly = true
      
      if (response.success && response.data) {
        setDepartments(response.data)
      } else {
        const errorMsg = response.error || "Failed to fetch departments"
        console.error('Error fetching departments:', response.error)
      }
    } catch (error) {
      const errorMsg = String(error)
      console.error('Error fetching departments:', errorMsg)
    }
  }

  useEffect(() => {
    
    const loadData = async () => {
      try {
        await Promise.all([
          fetchWorkCells(),
          fetchDepartments()
        ])
      } catch (error) {
        console.error('Error loading form data:', error)
      }
    }
    
    loadData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const onSubmit = async (data: WorkCellFormData) => {
    setIsSubmitting(true)
    
    try {
      // Data is already transformed by Zod schema (percentage to decimal)
      const response = await (async () => {
        if (editingId) {
          return await workCellService.update(editingId, data)
        } else {
          // Ensure name is present for create operations
          if (!data.name) {
            throw new Error('Name is required for creating work cells')
          }
          return await workCellService.create(data as WorkCellFormData & { name: string })
        }
      })()

      if (response.success) {
        toast({
          title: "Success",
          description: `Work cell ${editingId ? 'updated' : 'created'} successfully`
        })
        reset()
        setEditingId(null)
        fetchWorkCells()
      } else {
        const errorMsg = response.error || "Failed to save work cell"
        
        console.error('Error saving work cell:', response.error)
        toast({
          title: "Error",
          description: errorMsg,
          variant: "destructive"
        })
      }
    } catch (error) {
      const errorMsg = String(error)
      
      toast({
        title: "Error",
        description: "Failed to save work cell",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = (workCell: WorkCell) => {
    setEditingId(workCell.cell_id)
    setValue('name', workCell.name)
    setValue('capacity', workCell.capacity)
    setValue('department_id', workCell.department_id || '')
    setValue('wip_limit', workCell.wip_limit || 0)
    setValue('target_utilization', workCell.target_utilization * 100) // Convert decimal to %
    setValue('flow_priority', workCell.flow_priority)
    setValue('floor_location', workCell.floor_location || '')
    setValue('cell_type', workCell.cell_type as typeof cellTypes[number])
    setValue('is_active', workCell.is_active)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this work cell?')) return

    const response = await workCellService.delete(id)
    
    if (response.success) {
      toast({
        title: "Success",
        description: "Work cell deleted successfully"
      })
      fetchWorkCells()
    } else {
      console.error('Error deleting work cell:', response.error)
      toast({
        title: "Error",
        description: response.error || "Failed to delete work cell",
        variant: "destructive"
      })
    }
  }

  const handleCancel = () => {
    reset()
    setEditingId(null)
  }

  const sampleWorkCellData = {
    name: 'Assembly Line A',
    capacity: 5,
    department_id: null,
    wip_limit: 5,
    target_utilization: 0.85,
    flow_priority: 1,
    floor_location: 'Building A, Floor 2',
    cell_type: 'production',
    calendar_id: null,
    average_throughput_per_hour: 50,
    is_active: true
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="form" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="form">Single Entry</TabsTrigger>
          <TabsTrigger value="bulk">Mass Upload</TabsTrigger>
          {process.env.NODE_ENV === 'development' && (
            <TabsTrigger 
              value="performance"
              onClick={() => {
                // Performance monitoring removed
                setShowPerformanceDashboard(true)
              }}
            >
              Performance
            </TabsTrigger>
          )}
        </TabsList>
        
        <TabsContent value="form" className="space-y-6">
          {/* Form Card */}
          <Card>
        <CardHeader>
          <CardTitle>{editingId ? 'Edit Work Cell' : 'Create New Work Cell'}</CardTitle>
          <CardDescription>
            {editingId ? 'Update work cell information' : 'Add a new work cell for capacity and WIP constraints'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Name - Required */}
              <div className="space-y-2">
                <Label htmlFor="name">Cell Name *</Label>
                <Input
                  id="name"
                  {...register('name')}
                  placeholder="e.g., Production Cell A"
                  onBlur={(e) => {
                    validateField('name', e.target.value)
                  }}
                />
                {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
              </div>

              {/* Cell Type */}
              <div className="space-y-2">
                <Label htmlFor="cell_type">Cell Type</Label>
                <Select onValueChange={(value) => {
                  setValue('cell_type', value as typeof cellTypes[number])
                  /* Performance monitoring removed */
                  validateField('cell_type', value)
                }}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select cell type" />
                  </SelectTrigger>
                  <SelectContent>
                    {cellTypes.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type.charAt(0).toUpperCase() + type.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Department */}
              <div className="space-y-2">
                <Label htmlFor="department_id">Department</Label>
                <Select onValueChange={(value) => setValue('department_id', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select department" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No Department</SelectItem>
                    {departments.map((dept) => (
                      <SelectItem key={dept.department_id} value={dept.department_id}>
                        {dept.name} ({dept.code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Floor Location */}
              <div className="space-y-2">
                <Label htmlFor="floor_location">Floor Location</Label>
                <Input
                  id="floor_location"
                  {...register('floor_location')}
                  placeholder="e.g., Building A, Floor 2, Zone 3"
                />
              </div>

              {/* Capacity */}
              <div className="space-y-2">
                <Label htmlFor="capacity">Capacity</Label>
                <Input
                  id="capacity"
                  type="number"
                  min="1"
                  {...register('capacity', { valueAsNumber: true })}
                  onBlur={(e) => {
                    /* Performance monitoring removed */
                    validateField('capacity', parseInt(e.target.value))
                  }}
                />
                {errors.capacity && <p className="text-sm text-red-600">{errors.capacity.message}</p>}
              </div>

              {/* WIP Limit */}
              <div className="space-y-2">
                <Label htmlFor="wip_limit">WIP Limit</Label>
                <Input
                  id="wip_limit"
                  type="number"
                  min="0"
                  {...register('wip_limit', { valueAsNumber: true })}
                />
                <p className="text-xs text-gray-500">Work-in-progress limit for constraint generation</p>
                {errors.wip_limit && <p className="text-sm text-red-600">{errors.wip_limit.message}</p>}
              </div>

              {/* Target Utilization % */}
              <div className="space-y-2">
                <Label htmlFor="utilization_target_percent">Target Utilization (%)</Label>
                <Input
                  id="utilization_target_percent"
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  {...register('target_utilization', { valueAsNumber: true })}
                  placeholder="85.0"
                />
                <p className="text-xs text-gray-500">Target capacity utilization percentage for optimization</p>
                {errors.target_utilization && <p className="text-sm text-red-600">{errors.target_utilization.message}</p>}
              </div>

              {/* Flow Priority */}
              <div className="space-y-2">
                <Label htmlFor="flow_priority">Flow Priority</Label>
                <Input
                  id="flow_priority"
                  type="number"
                  min="1"
                  {...register('flow_priority', { 
                    valueAsNumber: true,
                    min: { value: 1, message: 'Priority must be at least 1' }
                  })}
                />
                <p className="text-xs text-gray-500">Higher numbers = higher priority</p>
                {errors.flow_priority && <p className="text-sm text-red-600">{errors.flow_priority.message}</p>}
              </div>
            </div>

            {/* Active Checkbox */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_active"
                checked={watch('is_active')}
                onCheckedChange={(checked) => setValue('is_active', !!checked)}
              />
              <Label htmlFor="is_active">Active</Label>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-2 pt-4">
              {editingId && (
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => {
                    /* Performance monitoring removed */
                    handleCancel()
                  }}
                >
                  Cancel
                </Button>
              )}
              <Button 
                type="submit" 
                disabled={isSubmitting}
              >
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {editingId ? 'Update' : 'Create'} Work Cell
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
        </TabsContent>
        
        <TabsContent value="bulk" className="space-y-6">
          <MassUploader
            tableName="work_cells"
            entityName="Work Cell"
            sampleData={sampleWorkCellData}
            onUploadComplete={fetchWorkCells}
            requiredFields={['name', 'capacity', 'cell_type']}
            fieldDescriptions={{
              name: 'Work cell display name',
              capacity: 'Maximum concurrent capacity',
              cell_type: 'Cell type (production, assembly, quality, etc.)',
              wip_limit: 'Work-in-progress limit',
              target_utilization: 'Target utilization (0.0 to 1.0)',
              flow_priority: 'Flow priority (higher = more important)'
            }}
          />
        </TabsContent>
        
        {process.env.NODE_ENV === 'development' && (
          <TabsContent value="performance" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>WorkCellForm Performance Monitoring</CardTitle>
                <CardDescription>
                  Real-time performance metrics for form load time, submission performance, 
                  field validation, user interactions, and error tracking.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Performance dashboard removed */}
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      {/* Work Cells List */}
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
            onBulkDelete={handleBulkDelete}
            onBulkEdit={handleBulkToggleActive}
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
                              onClick={() => {
                                /* Performance monitoring removed */
                                handleEdit(cell)
                              }}
                              disabled={loading}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                /* Performance monitoring removed */
                                handleBulkToggleActive([cell.cell_id])
                              }}
                              className={cell.is_active ? "text-orange-600 hover:bg-orange-50" : "text-green-600 hover:bg-green-50"}
                              disabled={loading}
                            >
                              {cell.is_active ? "Deactivate" : "Reactivate"}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                /* Performance monitoring removed */
                                handleDelete(cell.cell_id)
                              }}
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
    </div>
  )
}