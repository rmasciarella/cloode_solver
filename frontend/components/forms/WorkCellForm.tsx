"use client"

import { useWorkCellData } from './work-cells/useWorkCellData'
import { useWorkCellForm } from './work-cells/useWorkCellForm'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MassUploader } from '@/components/ui/mass-uploader'
import { WorkCellFormFields } from './work-cells/WorkCellFormFields'
import { WorkCellsTable } from './work-cells/WorkCellsTable'

export default function WorkCellForm() {
  const {
    workCells,
    departments,
    loading,
    fetchWorkCells
  } = useWorkCellData()

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    errors,
    editingId,
    isSubmitting,
    handleEdit,
    handleDelete,
    handleCancel
  } = useWorkCellForm()

  // Bulk operations handlers
  const handleBulkDelete = async (ids: string[]) => {
    for (const id of ids) {
      await handleDelete(id, fetchWorkCells)
    }
  }

  const handleBulkToggleActive = async (ids: string[]) => {
    // This would need to be implemented in the form hook
    console.log('Bulk toggle active for:', ids)
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
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="form">Single Entry</TabsTrigger>
          <TabsTrigger value="bulk">Mass Upload</TabsTrigger>
        </TabsList>
        
        <TabsContent value="form" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{editingId ? 'Edit Work Cell' : 'Create New Work Cell'}</CardTitle>
              <CardDescription>
                {editingId ? 'Update work cell information' : 'Add a new work cell for capacity and WIP constraints'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(fetchWorkCells)}>
                <WorkCellFormFields
                  register={register}
                  setValue={setValue}
                  watch={watch}
                  errors={errors}
                  departments={departments}
                  editingId={editingId}
                  isSubmitting={isSubmitting}
                  onCancel={handleCancel}
                />
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
      </Tabs>

      <WorkCellsTable
        workCells={workCells}
        departments={departments}
        onEdit={handleEdit}
        onDelete={(id) => handleDelete(id, fetchWorkCells)}
        onBulkDelete={handleBulkDelete}
        onBulkToggleActive={handleBulkToggleActive}
        loading={loading}
      />
    </div>
  )
}
}