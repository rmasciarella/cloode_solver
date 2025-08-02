"use client"

import { useState } from 'react'
import { Database } from '@/lib/database.types'
import { useJobTemplateData } from '@/hooks/forms/useJobTemplateData'
import { useJobTemplateForm } from '@/hooks/forms/useJobTemplateForm'
import { JobTemplateFormFields } from './job-templates/JobTemplateFormFields'
import { JobTemplatesTable } from './job-templates/JobTemplatesTable'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MassUploader } from '@/components/ui/mass-uploader'
import { AdvancedFilter, BulkOperations, useAdvancedTable } from '@/components/ui/advanced-patterns'
import { Loader2 } from 'lucide-react'
import { SkipLink, Announce } from './common/FormField'
import { useKeyboardNavigation } from '@/hooks/useKeyboardNavigation'

type JobTemplate = Database['public']['Tables']['job_optimized_patterns']['Row']

export default function JobTemplateForm() {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('form')
  
  // Data fetching
  const { jobTemplates, loading, fetchJobTemplates } = useJobTemplateData()
  
  // Form management
  const {
    form,
    isSubmitting,
    handleSubmit,
    handleDelete,
    handleToggleActive,
    performanceTracker,
    defaultSolverParameters
  } = useJobTemplateForm(
    () => {
      setEditingId(null)
      fetchJobTemplates()
    },
    editingId
  )

  // Advanced table functionality
  const advancedTable = useAdvancedTable(
    jobTemplates,
    (template) => template.pattern_id,
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
    { key: 'description', label: 'Description', type: 'text' as const },
    { key: 'is_active', label: 'Active', type: 'boolean' as const }
  ]

  // Bulk operations handlers
  const handleBulkDelete = async (ids: string[]) => {
    performanceTracker.trackInteraction('click', 'bulk_delete')
    
    for (const id of ids) {
      const template = jobTemplates.find(t => t.pattern_id === id)
      if (template) {
        await handleDelete(id, template.name)
      }
    }
    advancedTable.clearSelection()
  }

  const handleBulkToggleActive = async (ids: string[]) => {
    performanceTracker.trackInteraction('click', 'bulk_toggle_active')
    
    for (const id of ids) {
      const template = jobTemplates.find(t => t.pattern_id === id)
      if (template) {
        await handleToggleActive(id, template.name, template.is_active)
      }
    }
    advancedTable.clearSelection()
  }

  const handleEdit = (template: JobTemplate) => {
    performanceTracker.trackInteraction('click', 'edit_template')
    
    setEditingId(template.pattern_id)
    form.setValue('name', template.name)
    form.setValue('description', template.description || '')
    // Fix: Convert solver_parameters object to JSON string for the textarea
    form.setValue('solver_parameters', typeof template.solver_parameters === 'object' 
      ? JSON.stringify(template.solver_parameters, null, 2)
      : String(template.solver_parameters))
    form.setValue('task_count', template.task_count || 1)
    form.setValue('total_min_duration_minutes', template.total_min_duration_minutes || 60)
    form.setValue('critical_path_length_minutes', template.critical_path_length_minutes || 60)
    
    setActiveTab('form')
  }

  const handleCancel = () => {
    performanceTracker.trackInteraction('click', 'cancel')
    form.reset()
    setEditingId(null)
  }

  const sampleJobTemplateData = {
    name: 'Standard Assembly Job',
    description: 'Standard assembly process for product line A',
    department_id: null,
    estimated_duration_minutes: 120,
    priority_weight: 1.0,
    solver_parameters: defaultSolverParameters,
    is_active: true
  }

  return (
    <div className="space-y-6">
      <SkipLink href="#job-template-list">Skip to job template list</SkipLink>
      
      {/* Screen reader announcements */}
      {isSubmitting && <Announce message="Submitting job template form" priority="polite" />}
      {loading && <Announce message="Loading job templates" priority="polite" />}
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger 
            value="form" 
            onClick={() => performanceTracker.trackInteraction('click', 'button_click')}
          >
            Single Entry
          </TabsTrigger>
          <TabsTrigger 
            value="bulk" 
            onClick={() => performanceTracker.trackInteraction('click', 'button_click')}
          >
            Mass Upload
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="form" className="space-y-6">
          {/* Form Card */}
          <Card>
            <CardHeader>
              <CardTitle>{editingId ? 'Edit Job Template' : 'Create New Job Template'}</CardTitle>
              <CardDescription>
                {editingId 
                  ? 'Update job template information' 
                  : 'Add a reusable job template for manufacturing scheduling'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
                <JobTemplateFormFields
                  form={form}
                  onFieldFocus={performanceTracker.trackFieldFocus}
                  defaultSolverParameters={defaultSolverParameters}
                />
                
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
                    onClick={() => performanceTracker.trackInteraction('click', 'button_click')}
                  >
                    {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    {editingId ? 'Update' : 'Create'} Template
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="bulk" className="space-y-6">
          <MassUploader
            tableName="job_optimized_patterns"
            entityName="Job Template"
            sampleData={sampleJobTemplateData}
            onUploadComplete={() => {
              performanceTracker.trackInteraction('click', 'upload_complete')
              fetchJobTemplates()
            }}
            requiredFields={['name']}
            fieldDescriptions={{
              name: 'Template display name',
              description: 'Template description',
              estimated_duration_minutes: 'Expected duration in minutes',
              priority_weight: 'Priority weight (1.0 = normal)',
              solver_parameters: 'JSON object with solver parameters'
            }}
          />
        </TabsContent>
      </Tabs>

      {/* Templates List */}
      <Card id="job-template-list">
        <CardHeader>
          <CardTitle>Job Templates ({advancedTable.filteredCount} of {advancedTable.totalCount})</CardTitle>
          <CardDescription>Manage existing job templates with advanced filtering and bulk operations</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Advanced Filter */}
          <AdvancedFilter
            options={filterOptions}
            values={advancedTable.filters}
            onChange={(filters) => {
              performanceTracker.trackInteraction('click', 'filter_change')
              advancedTable.setFilters(filters)
            }}
            placeholder="Search job templates..."
          />

          {/* Bulk Operations */}
          <BulkOperations
            items={advancedTable.filteredItems}
            selectedItems={advancedTable.selectedItems}
            onToggleSelection={(id) => {
              performanceTracker.trackInteraction('click', 'toggle_selection')
              advancedTable.toggleSelection(id)
            }}
            onSelectAll={() => {
              performanceTracker.trackInteraction('click', 'select_all')
              advancedTable.selectAll()
            }}
            onClearSelection={() => {
              performanceTracker.trackInteraction('click', 'clear_selection')
              advancedTable.clearSelection()
            }}
            onBulkDelete={handleBulkDelete}
            onBulkEdit={handleBulkToggleActive}
            getId={(template) => template.pattern_id}
            isSelectionMode={advancedTable.isSelectionMode}
            onEnterSelectionMode={() => {
              performanceTracker.trackInteraction('click', 'enter_selection_mode')
              advancedTable.enterSelectionMode()
            }}
          />

          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : advancedTable.isEmpty ? (
            <p className="text-center text-gray-500 py-4">
              {advancedTable.filters.length > 0 ? 'No job templates match your filters' : 'No job templates found'}
            </p>
          ) : (
            <JobTemplatesTable
              jobTemplates={advancedTable.filteredItems}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onToggleActive={handleToggleActive}
              loading={loading}
              selectedItems={advancedTable.selectedItems}
              onToggleSelection={advancedTable.toggleSelection}
              isSelectionMode={advancedTable.isSelectionMode}
              onSort={advancedTable.setSortBy}
              trackInteraction={performanceTracker.trackInteraction}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}