"use client"

import { useState, useEffect, useCallback, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { departmentService } from '@/lib/services'
import { departmentFormSchema, type DepartmentFormData } from '@/lib/schemas'
import { Database } from '@/lib/database.types'
import { useToast } from '@/hooks/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TimeInput } from '@/components/ui/time-input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MassUploader } from '@/components/ui/mass-uploader'
import { AdvancedFilter, BulkOperations, useAdvancedTable } from '@/components/ui/advanced-patterns'
import { indexToTime12, getTimeRangeDescription } from '@/lib/timeUtils'
import { performanceMonitor } from '@/lib/performance/monitoring'
import { Loader2, Plus, Edit, Trash2, Upload, Search, Filter } from 'lucide-react'

type Department = Database['public']['Tables']['departments']['Row']

// Performance monitoring removed to fix hydration errors

export default function DepartmentForm() {
  const [departments, setDepartments] = useState<Department[]>([])
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()
  
  // Performance tracking removed to fix hydration errors

  // Advanced table functionality
  const advancedTable = useAdvancedTable(
    departments,
    (dept) => dept.department_id,
    {
      enableFiltering: true,
      enableBulkOperations: true,
      enableSorting: true
    }
  )

  const filterOptions = [
    { key: 'name', label: 'Name', type: 'text' as const },
    { key: 'code', label: 'Code', type: 'text' as const },
    { key: 'cost_center', label: 'Cost Center', type: 'text' as const },
    { key: 'is_active', label: 'Active', type: 'boolean' as const },
    { key: 'overtime_allowed', label: 'Overtime Allowed', type: 'boolean' as const }
  ]

  // Bulk operations handlers
  const handleBulkDelete = async (ids: string[]) => {
    for (const id of ids) {
      const response = await departmentService.delete(id)
      if (!response.success) {
        toast({
          title: "Error",
          description: `Failed to delete department: ${response.error}`,
          variant: "destructive"
        })
        return
      }
    }
    toast({
      title: "Success",
      description: `Successfully deleted ${ids.length} departments`
    })
    fetchDepartments()
    advancedTable.clearSelection()
  }

  const handleBulkToggleActive = async (ids: string[]) => {
    for (const id of ids) {
      const dept = departments.find(d => d.department_id === id)
      if (dept) {
        const response = await departmentService.update(id, { is_active: !dept.is_active })
        if (!response.success) {
          toast({
            title: "Error",
            description: `Failed to update department: ${response.error}`,
            variant: "destructive"
          })
          return
        }
      }
    }
    toast({
      title: "Success",
      description: `Successfully updated ${ids.length} departments`
    })
    fetchDepartments()
    advancedTable.clearSelection()
  }

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<DepartmentFormData>({
    resolver: zodResolver(departmentFormSchema),
    defaultValues: {
      code: '',
      name: '',
      description: '',
      parent_department_id: '',
      cost_center: '',
      default_shift_start: 32, // 8 AM
      default_shift_end: 64,   // 4 PM
      overtime_allowed: true,
      is_active: true
    }
  })
  
  // Performance tracking removed to fix hydration errors

  const fetchDepartments = useCallback(async () => {
    setLoading(true)
    const startTime = performance.now()
    
    try {
      const response = await departmentService.getAll()
      
      // Record data loading performance
      const loadTime = performance.now() - startTime
      if (process.env.NODE_ENV === 'development') {
        console.log(`[FORM-PERF] DepartmentForm data load: ${loadTime}ms`)
      }
      
      if (response.success && response.data) {
        setDepartments(response.data)
      } else {
        console.error('Error fetching departments:', response.error)
        // Performance tracking removed
        toast({
          title: "Error",
          description: response.error || "Failed to fetch departments",
          variant: "destructive"
        })
      }
    } catch (error) {
      // Performance tracking removed
      console.error('Error in fetchDepartments:', error)
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    fetchDepartments()
  }, [])

  const onSubmit = async (data: DepartmentFormData) => {
    setIsSubmitting(true)
    // Performance tracking removed
    
    try {
      // Performance tracking removed
      
      // Ensure required fields are present
      const submitData = {
        ...data,
        code: data.code || '',
        name: data.name || ''
      }
      
      // Performance tracking removed
      
      let response
      if (editingId) {
        response = await departmentService.update(editingId, submitData)
      } else {
        response = await departmentService.create(submitData)
      }

      if (response.success) {
        // Performance tracking removed
        
        toast({
          title: "Success",
          description: `Department ${editingId ? 'updated' : 'created'} successfully`
        })
        reset()
        setEditingId(null)
        fetchDepartments()
      } else {
        // Performance tracking removed
        
        console.error('Error saving department:', response.error)
        
        // Handle specific database errors
        let errorMessage = response.error || "Failed to save department"
        if (response.error?.includes('duplicate key value violates unique constraint') && 
            response.error?.includes('departments_code_key')) {
          errorMessage = `Department code "${data.code}" already exists. Please use a different code.`
        } else if (response.error?.includes('duplicate key') && response.error?.includes('code')) {
          errorMessage = `This department code is already in use. Please choose a unique code.`
        }
        
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive"
        })
      }
    } catch (error) {
      // Performance tracking removed
      console.error('Error in onSubmit:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = (department: Department) => {
    // Performance tracking removed
    
    setEditingId(department.department_id)
    setValue('code', department.code)
    setValue('name', department.name)
    setValue('description', department.description || '')
    setValue('parent_department_id', department.parent_department_id || 'none')
    setValue('cost_center', department.cost_center || '')
    setValue('default_shift_start', department.default_shift_start)
    setValue('default_shift_end', department.default_shift_end)
    setValue('overtime_allowed', department.overtime_allowed)
    setValue('is_active', department.is_active)
  }

  const handleDelete = async (id: string) => {
    // Performance tracking removed
    
    const department = departments.find(d => d.department_id === id)
    if (!department) return

    if (!confirm(`Are you sure you want to delete "${department.name}"?\n\nThis action cannot be undone.`)) return

    const startTime = performance.now()
    const response = await departmentService.delete(id)
    const deleteTime = performance.now() - startTime
    if (process.env.NODE_ENV === 'development') {
      console.log(`[FORM-PERF] DepartmentForm delete: ${deleteTime}ms`)
    }
    
    if (response.success) {
      toast({
        title: "Success",
        description: `Department "${department.name}" deleted successfully`
      })
      fetchDepartments()
    } else {
      console.error('Error deleting department:', response.error)
      
      let errorMessage = response.error || "Failed to delete department"
      let errorDetails = ""
      
      // Check for common constraint violation errors
      if (response.error?.includes('foreign key constraint') || 
          response.error?.includes('violates foreign key')) {
        errorMessage = "Cannot delete department - it's still in use"
        errorDetails = "This department has related records (job instances, operators, etc.). Either delete those first or deactivate this department instead."
      } else if (response.error?.includes('dependent')) {
        errorMessage = "Cannot delete department - has dependencies"
        errorDetails = "Other departments or records depend on this one. Consider deactivating instead."
      }

      toast({
        title: "Error",
        description: errorDetails || errorMessage,
        variant: "destructive"
      })
    }
  }

  const handleToggleActive = async (id: string) => {
    // Performance tracking removed
    
    const department = departments.find(d => d.department_id === id)
    if (!department) return

    const newStatus = !department.is_active
    const action = newStatus ? 'reactivate' : 'deactivate'
    
    if (!confirm(`Are you sure you want to ${action} "${department.name}"?`)) return

    const startTime = performance.now()
    const response = await departmentService.toggleActive(id)
    const toggleTime = performance.now() - startTime
    if (process.env.NODE_ENV === 'development') {
      console.log(`[FORM-PERF] DepartmentForm toggle: ${toggleTime}ms`)
    }
    
    if (response.success) {
      toast({
        title: "Success",
        description: `Department "${department.name}" ${newStatus ? 'reactivated' : 'deactivated'} successfully`
      })
      fetchDepartments()
    } else {
      console.error(`Error ${action}ing department:`, response.error)
      toast({
        title: "Error",
        description: response.error || `Failed to ${action} department`,
        variant: "destructive"
      })
    }
  }

  const handleCancel = () => {
    // Performance tracking removed
    reset()
    setEditingId(null)
  }

  const sampleDepartmentData = {
    code: 'PROD',
    name: 'Production Department',
    description: 'Main production operations',
    parent_department_id: null,
    cost_center: 'CC-PROD-001',
    default_shift_start: 32, // 8:00 AM
    default_shift_end: 64,   // 4:00 PM
    overtime_allowed: true,
    is_active: true
  }


  // Allow all departments as potential parents, but prevent circular references
  const parentDepartments = departments.filter(dept => {
    // When creating new department, show all departments
    if (!editingId) return true
    
    // When editing, exclude self to prevent self-reference
    if (dept.department_id === editingId) return false
    
    // TODO: Add circular reference prevention logic here
    // For now, just prevent direct self-reference
    return true
  })

  return (
    <div className="space-y-6">
      {/* Tabs for Single Entry and Bulk Upload */}
      <Tabs defaultValue="form" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="form">Single Entry</TabsTrigger>
          <TabsTrigger value="bulk">Mass Upload</TabsTrigger>
        </TabsList>
        
        <TabsContent value="form" className="space-y-6">
          {/* Form Card */}
          <Card>
        <CardHeader>
          <CardTitle>{editingId ? 'Edit Department' : 'Create New Department'}</CardTitle>
          <CardDescription>
            {editingId ? 'Update department information and hierarchy' : 'Create a department - use "None (Root Department)" for standalone departments or select a parent for hierarchy'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Code - Required */}
              <div className="space-y-2">
                <Label htmlFor="code">Code *</Label>
                <Input
                  id="code"
                  {...register('code', { 
                    required: 'Department code is required',
                    maxLength: { value: 50, message: 'Code must be 50 characters or less' }
                  })}
                  placeholder="e.g., production, quality, DEPT_A"
                  // Performance tracking removed
                />
                {errors.code && <p className="text-sm text-red-600">{errors.code.message}</p>}
                <p className="text-xs text-gray-500">Must be unique across all departments</p>
              </div>

              {/* Name - Required */}
              <div className="space-y-2">
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  {...register('name', { 
                    required: 'Department name is required',
                    maxLength: { value: 255, message: 'Name must be 255 characters or less' }
                  })}
                  placeholder="e.g., Production Department"
                  // Performance tracking removed
                />
                {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
              </div>

              {/* Parent Department */}
              <div className="space-y-2">
                <Label htmlFor="parent_department_id">Parent Department</Label>
                <Select 
                  value={watch('parent_department_id') || undefined}
                  onValueChange={(value) => {
                    setValue('parent_department_id', value)
                  }}
                >
                  <SelectTrigger id="parent_department_id">
                    <SelectValue placeholder="Select parent department" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None (Root Department)</SelectItem>
                    {parentDepartments.map((dept) => (
                      <SelectItem key={dept.department_id} value={dept.department_id}>
                        {dept.name} ({dept.code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500">
                  <strong>For single department use:</strong> Select &quot;None (Root Department)&quot; to make this a top-level department.<br/>
                  <strong>For hierarchy:</strong> Child departments inherit scheduling constraints from parent.
                </p>
              </div>

              {/* Cost Center */}
              <div className="space-y-2">
                <Label htmlFor="cost_center">Cost Center Code</Label>
                <Input
                  id="cost_center"
                  {...register('cost_center')}
                  placeholder="e.g., CC-PROD-001"
                  // Performance tracking removed
                />
                <p className="text-xs text-gray-500">
                  Optional: For financial tracking and cost allocation (not currently mapped to solver constraints)
                </p>
              </div>

              {/* Shift Start Time */}
              <TimeInput
                label="Default Shift Start Time"
                value={watch('default_shift_start') || 32}
                onChange={(index) => {
                  setValue('default_shift_start', index)
                }}
                id="default_shift_start"
                placeholder="Select start time"
                helperText="Default start time for this department's shifts"
                required
              />

              {/* Shift End Time */}
              <TimeInput
                label="Default Shift End Time"
                value={watch('default_shift_end') || 64}
                onChange={(index) => {
                  setValue('default_shift_end', index)
                }}
                id="default_shift_end"
                placeholder="Select end time"
                helperText="Default end time for this department's shifts"
                required
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                {...register('description')}
                placeholder="Department description and responsibilities"
                rows={3}
                // Performance tracking removed
              />
            </div>

            {/* Checkboxes */}
            <div className="flex flex-col space-y-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="overtime_allowed"
                  checked={watch('overtime_allowed')}
                  onCheckedChange={(checked) => {
                    setValue('overtime_allowed', checked as boolean)
                  }}
                />
                <Label htmlFor="overtime_allowed">Overtime Allowed</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_active"
                  checked={watch('is_active')}
                  onCheckedChange={(checked) => {
                    setValue('is_active', checked as boolean)
                  }}
                />
                <Label htmlFor="is_active">Active</Label>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-2 pt-4">
              {editingId && (
                <Button type="button" variant="outline" onClick={handleCancel}>
                  Cancel
                </Button>
              )}
              <Button 
                type="submit" 
                disabled={isSubmitting}
                // Performance tracking removed
              >
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {editingId ? 'Update' : 'Create'} Department
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
        </TabsContent>
        
        <TabsContent value="bulk" className="space-y-6">
          <MassUploader
            tableName="departments"
            entityName="Department"
            sampleData={sampleDepartmentData}
            onUploadComplete={fetchDepartments}
            requiredFields={['code', 'name']}
            fieldDescriptions={{
              code: 'Unique department code',
              name: 'Department display name',
              default_shift_start: 'Start time (15-min intervals from midnight)',
              default_shift_end: 'End time (15-min intervals from midnight)'
            }}
          />
        </TabsContent>
      </Tabs>

      {/* Advanced Departments List */}
      <Card>
        <CardHeader>
          <CardTitle>Departments ({advancedTable.filteredCount} of {advancedTable.totalCount})</CardTitle>
          <CardDescription>Manage existing departments with advanced filtering and bulk operations</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Advanced Filter */}
          <AdvancedFilter
            options={filterOptions}
            values={advancedTable.filters}
            onChange={advancedTable.setFilters}
            placeholder="Search departments..."
          />

          {/* Bulk Operations */}
          <BulkOperations
            items={advancedTable.filteredItems}
            selectedItems={advancedTable.selectedItems}
            onToggleSelection={advancedTable.toggleSelection}
            onSelectAll={advancedTable.selectAll}
            onClearSelection={advancedTable.clearSelection}
            onBulkDelete={handleBulkDelete}
            onBulkEdit={handleBulkToggleActive}
            getId={(dept) => dept.department_id}
            isSelectionMode={advancedTable.isSelectionMode}
            onEnterSelectionMode={advancedTable.enterSelectionMode}
          />

          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : advancedTable.isEmpty ? (
            <p className="text-center text-gray-500 py-4">
              {advancedTable.filters.length > 0 ? 'No departments match your filters' : 'No departments found'}
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
                              advancedTable.selectAll(advancedTable.filteredItems, (dept) => dept.department_id)
                            }
                          }}
                          className="rounded"
                        />
                      </th>
                    )}
                    <th className="text-left p-2 font-medium cursor-pointer hover:bg-gray-50" onClick={() => advancedTable.setSortBy('code')}>Code ↕</th>
                    <th className="text-left p-2 font-medium cursor-pointer hover:bg-gray-50" onClick={() => advancedTable.setSortBy('name')}>Name ↕</th>
                    <th className="text-left p-2 font-medium">Cost Center</th>
                    <th className="text-left p-2 font-medium">Shift Times</th>
                    <th className="text-left p-2 font-medium">Status</th>
                    <th className="text-left p-2 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {advancedTable.filteredItems.map((department) => (
                    <tr key={department.department_id} className="border-b hover:bg-gray-50">
                      {advancedTable.isSelectionMode && (
                        <td className="p-2">
                          <input
                            type="checkbox"
                            checked={advancedTable.selectedItems.has(department.department_id)}
                            onChange={() => advancedTable.toggleSelection(department.department_id)}
                            className="rounded"
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
                            onClick={() => handleEdit(department)}
                            disabled={loading}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleBulkToggleActive([department.department_id])}
                            className={department.is_active ? "text-orange-600 hover:bg-orange-50" : "text-green-600 hover:bg-green-50"}
                            disabled={loading}
                          >
                            {department.is_active ? "Deactivate" : "Reactivate"}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDelete(department.department_id)}
                            className="text-red-600 hover:bg-red-50"
                            disabled={loading}
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
          )}
        </CardContent>
      </Card>
    </div>
  )
}