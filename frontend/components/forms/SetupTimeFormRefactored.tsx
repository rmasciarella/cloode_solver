"use client"

import { Card } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MassUploader } from '@/components/ui/mass-uploader'
import { PerformanceDashboard } from '@/components/ui/performance-dashboard'
import { useSetupTimeData } from '@/hooks/forms/useSetupTimeData'
import { useSetupTimeForm } from '@/hooks/forms/useSetupTimeForm'
import { SetupTimeFormHeader } from './setup-times/SetupTimeFormHeader'
import { SetupTimeFormDialog } from './setup-times/SetupTimeFormDialog'
import { SetupTimeDataTable } from './setup-times/SetupTimeDataTable'

const sampleSetupTimeData = {
  from_optimized_task_id: '',
  to_optimized_task_id: '',
  machine_resource_id: '',
  setup_time_minutes: 30,
  teardown_time_minutes: 15,
  changeover_cost: 25.0,
  complexity_factor: 1.2,
  is_active: true
}

export default function SetupTimeFormRefactored() {
  const {
    setupTimes,
    templateTasks,
    machines,
    loading,
    fetchSetupTimes,
    deleteSetupTime
  } = useSetupTimeData()

  const {
    form,
    editingId,
    isSubmitting,
    onSubmit,
    handleEdit,
    handleCancel,
    handleFieldFocus,
    handleFieldBlur,
    handleFieldChange,
    monitor
  } = useSetupTimeForm(fetchSetupTimes)

  return (
    <div className="space-y-6">
      <Tabs defaultValue="form" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="form">Single Entry</TabsTrigger>
          <TabsTrigger value="bulk">Mass Upload</TabsTrigger>
        </TabsList>
        
        <TabsContent value="form" className="space-y-6">
          <Card>
            <SetupTimeFormHeader editingId={editingId} />
            <SetupTimeFormDialog
              form={form}
              templateTasks={templateTasks}
              machines={machines}
              editingId={editingId}
              isSubmitting={isSubmitting}
              onSubmit={onSubmit}
              onCancel={handleCancel}
              onFieldFocus={handleFieldFocus}
              onFieldBlur={handleFieldBlur}
              onFieldChange={handleFieldChange}
            />
          </Card>
        </TabsContent>
        
        <TabsContent value="bulk" className="space-y-6">
          <MassUploader
            tableName="optimized_task_setup_times"
            entityName="Setup Time"
            sampleData={sampleSetupTimeData}
            onUploadComplete={fetchSetupTimes}
            requiredFields={['from_optimized_task_id', 'to_optimized_task_id', 'machine_resource_id', 'setup_time_minutes']}
            fieldDescriptions={{
              from_optimized_task_id: 'Source task ID',
              to_optimized_task_id: 'Target task ID',
              machine_resource_id: 'Machine ID (required)',
              setup_time_minutes: 'Setup duration in minutes',
              teardown_time_minutes: 'Teardown duration in minutes',
              changeover_cost: 'Cost of changeover operation'
            }}
          />
        </TabsContent>
      </Tabs>

      {process.env.NODE_ENV === 'development' && (
        <Card>
          <PerformanceDashboard monitor={monitor} />
        </Card>
      )}

      <SetupTimeDataTable
        setupTimes={setupTimes}
        loading={loading}
        onEdit={handleEdit}
        onDelete={deleteSetupTime}
      />
    </div>
  )
}