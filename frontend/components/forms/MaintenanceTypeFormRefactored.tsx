"use client"

import { Card } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MassUploader } from '@/components/ui/mass-uploader'
import { useMaintenanceTypeData } from '@/hooks/forms/useMaintenanceTypeData'
import { useMaintenanceTypeForm } from '@/hooks/forms/useMaintenanceTypeForm'
import { MaintenanceTypeFormHeader } from './maintenance-types/MaintenanceTypeFormHeader'
import { MaintenanceTypeFormDialog } from './maintenance-types/MaintenanceTypeFormDialog'
import { MaintenanceTypeDataTable } from './maintenance-types/MaintenanceTypeDataTable'

const sampleMaintenanceTypeData = {
  name: 'Monthly Preventive',
  description: 'Regular monthly maintenance check',
  is_preventive: true,
  is_emergency: false,
  typical_duration_hours: 4,
  blocks_production: true,
  allows_emergency_override: false,
  requires_shutdown: true,
  required_skill_level: 'PROFICIENT',
  requires_external_vendor: false
}

export default function MaintenanceTypeFormRefactored() {
  const {
    maintenanceTypes,
    loading,
    fetchMaintenanceTypes,
    deleteMaintenanceType
  } = useMaintenanceTypeData()

  const {
    form,
    editingId,
    isSubmitting,
    onSubmit,
    handleEdit,
    handleCancel,
    handleFieldInteraction,
    performanceMonitor: _performanceMonitor
  } = useMaintenanceTypeForm(fetchMaintenanceTypes)

  return (
    <div className="space-y-6">
      <Tabs defaultValue="form" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="form">Single Entry</TabsTrigger>
          <TabsTrigger value="bulk">Mass Upload</TabsTrigger>
        </TabsList>
        
        <TabsContent value="form" className="space-y-6">
          <Card>
            <MaintenanceTypeFormHeader editingId={editingId} />
            <MaintenanceTypeFormDialog
              form={form}
              editingId={editingId}
              isSubmitting={isSubmitting}
              onSubmit={onSubmit}
              onCancel={handleCancel}
              onFieldInteraction={handleFieldInteraction}
            />
          </Card>
        </TabsContent>
        
        <TabsContent value="bulk" className="space-y-6">
          <MassUploader
            tableName="maintenance_types"
            entityName="Maintenance Type"
            sampleData={sampleMaintenanceTypeData}
            onUploadComplete={fetchMaintenanceTypes}
            requiredFields={['name', 'typical_duration_hours']}
            fieldDescriptions={{
              name: 'Maintenance type name',
              description: 'Description of the maintenance',
              is_preventive: 'true/false - Is this preventive maintenance?',
              is_emergency: 'true/false - Is this emergency maintenance?',
              typical_duration_hours: 'Expected duration in hours',
              blocks_production: 'true/false - Does it block production?',
              allows_emergency_override: 'true/false - Can be overridden?',
              requires_shutdown: 'true/false - Requires shutdown?',
              required_skill_level: 'NOVICE/COMPETENT/PROFICIENT/EXPERT',
              requires_external_vendor: 'true/false - Needs external vendor?'
            }}
          />
        </TabsContent>
      </Tabs>

      <MaintenanceTypeDataTable
        maintenanceTypes={maintenanceTypes}
        loading={loading}
        onEdit={handleEdit}
        onDelete={deleteMaintenanceType}
      />
    </div>
  )
}