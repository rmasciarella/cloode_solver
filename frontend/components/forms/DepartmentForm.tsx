"use client"

import { useState } from 'react'
import { Database } from '@/lib/database.types'
import { useToast } from '@/hooks/use-toast'
import { useFormPerformance } from '@/lib/hooks/use-form-performance'
import { useDepartmentData } from '@/hooks/forms/useDepartmentData'
import { useDepartmentForm } from '@/hooks/forms/useDepartmentForm'
import { DepartmentFormFields } from './departments/DepartmentFormFields'
import { DepartmentsTable } from './departments/DepartmentsTable'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MassUploader } from '@/components/ui/mass-uploader'
import { AdvancedFilter, BulkOperations, useAdvancedTable } from '@/components/ui/advanced-patterns'
import { Loader2 } from 'lucide-react'
import { SkipLink, Announce } from './common/FormField'
import { useKeyboardNavigation } from '@/hooks/useKeyboardNavigation'

type Department = Database['public']['Tables']['departments']['Row']

export default function DepartmentForm() {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('form')
  const { toast } = useToast()
  
  // Performance monitoring
  const { trackInteraction, trackFieldFocus } = useFormPerformance('DepartmentForm')
  
  // Data fetching
  const { departments, loading, fetchDepartments } = useDepartmentData()
  
  // Form management
  const {
    form,
    isSubmitting,
    handleSubmit,
    handleDelete,
    handleToggleActive
  } = useDepartmentForm(
    () => {
      setEditingId(null)
      fetchDepartments()
    },
    editingId
  )

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

  // Keyboard navigation
  useKeyboardNavigation({
    onEscape: () => {
      if (editingId) {
        handleCancel()
      } else {
        setActiveTab('form')
      }
    },
    onEnter: () => {
      if (activeTab === 'form') {
        form.handleSubmit(handleSubmit)()
      }
    }
  })

  const filterOptions = [
    { key: 'name', label: 'Name', type: 'text' as const },
    { key: 'code', label: 'Code', type: 'text' as const },
    { key: 'cost_center', label: 'Cost Center', type: 'text' as const },
    { key: 'is_active', label: 'Active', type: 'boolean' as const },
    { key: 'overtime_allowed', label: 'Overtime Allowed', type: 'boolean' as const }
  ]

  // Bulk operations handlers
  const handleBulkDelete = async (ids: string[]) => {
    trackInteraction('click', 'bulk_delete')
    
    for (const id of ids) {
      const dept = departments.find(d => d.department_id === id)
      if (dept) {
        await handleDelete(id, dept.name)
      }
    }
    advancedTable.clearSelection()
  }

  const handleBulkToggleActive = async (ids: string[]) => {
    trackInteraction('click', 'bulk_toggle_active')
    
    for (const id of ids) {
      const dept = departments.find(d => d.department_id === id)
      if (dept) {
        await handleToggleActive(id, dept.name, dept.is_active)
      }
    }
    advancedTable.clearSelection()
  }

  const handleEdit = (department: Department) => {
    trackInteraction('click', 'edit_department')
    setEditingId(department.department_id)
    
    form.setValue('code', department.code)
    form.setValue('name', department.name)
    form.setValue('description', department.description || '')
    form.setValue('parent_department_id', department.parent_department_id || 'none')
    form.setValue('cost_center', department.cost_center || '')
    form.setValue('default_shift_start', department.default_shift_start)
    form.setValue('default_shift_end', department.default_shift_end)
    form.setValue('overtime_allowed', department.overtime_allowed)
    form.setValue('is_active', department.is_active)
    
    setActiveTab('form')
  }

  const handleCancel = () => {
    trackInteraction('click', 'cancel')
    form.reset()
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

  return (
    <div className="space-y-6">
      <SkipLink href="#department-list">Skip to department list</SkipLink>
      
      {/* Screen reader announcements */}
      {isSubmitting && <Announce message="Submitting department form" priority="polite" />}
      {loading && <Announce message="Loading departments" priority="polite" />}
      
      {/* Tabs for Single Entry and Bulk Upload */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger 
            value="form" 
            onClick={() => trackInteraction('click', 'tab_single_entry')}
          >
            Single Entry
          </TabsTrigger>
          <TabsTrigger 
            value="bulk" 
            onClick={() => trackInteraction('click', 'tab_bulk_upload')}
          >
            Mass Upload
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="form" className="space-y-6">
          {/* Form Card */}
          <Card>
            <CardHeader>
              <CardTitle>{editingId ? 'Edit Department' : 'Create New Department'}</CardTitle>
              <CardDescription>
                {editingId 
                  ? 'Update department information and hierarchy' 
                  : 'Create a department - use "None (Root Department)" for standalone departments or select a parent for hierarchy'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
                <DepartmentFormFields
                  form={form}
                  departments={departments}
                  editingId={editingId}
                  onFieldFocus={trackFieldFocus}
                />
                
                {/* Action Buttons */}
                <div className="flex justify-end space-x-2 pt-4">
                  {editingId && (
                    <Button 
                      type="button" 
                      variant="outline" 
                      onClick={handleCancel}
                    >
                      Cancel
                    </Button>
                  )}
                  <Button 
                    type="submit" 
                    disabled={isSubmitting}
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
      <Card id="department-list">
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
            <DepartmentsTable
              departments={advancedTable.filteredItems}
              onEdit={handleEdit}
              onDelete={(id, name) => {
                trackInteraction('click', 'delete_department')
                handleDelete(id, name)
              }}
              onToggleActive={(id, name, isActive) => {
                trackInteraction('click', 'toggle_department_active')
                handleToggleActive(id, name, isActive)
              }}
              loading={loading}
              selectedItems={advancedTable.selectedItems}
              onToggleSelection={advancedTable.toggleSelection}
              isSelectionMode={advancedTable.isSelectionMode}
              onSort={advancedTable.setSortBy}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}