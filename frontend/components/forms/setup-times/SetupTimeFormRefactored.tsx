"use client"

import { useState, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { optimizedTaskSetupTimeService, optimizedTaskService, machineService } from '@/lib/services'
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'
import { MassUploader } from '@/components/ui/mass-uploader'
import { FormLayout } from '@/components/forms/common/FormLayout'
import { 
  useFormPerformance, 
  useFormData, 
  useFormSubmission,
  useMultipleFormData 
} from '@/hooks/forms'
import { SetupTimeFormFields } from './SetupTimeFormFields'
import { SetupTimesTable } from './SetupTimesTable'
import { Database } from '@/lib/database.types'

// Use the database type
type DatabaseSetupTime = Database['public']['Tables']['optimized_task_setup_times']['Row']
type DatabaseOptimizedTask = Database['public']['Tables']['optimized_tasks']['Row']
type DatabaseMachine = Database['public']['Tables']['machines']['Row']

interface SetupTimeFormData {
  from_optimized_task_id: string
  to_optimized_task_id: string
  machine_resource_id: string
  setup_time_minutes: number
  setup_type: string
  complexity_level: string
  requires_operator_skill: string
  requires_certification: boolean
  requires_supervisor_approval: boolean
  setup_cost: number
  efficiency_impact_percent: number
  product_family_from: string
  product_family_to: string
}

// SetupTime type that matches SetupTimesTable expectations
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

// Task type for display
interface UIOptimizedTask {
  optimized_task_id: string
  task_name: string
  pattern_name: string
  pattern_id: string
}

// Machine type for display with required setup_time_minutes
interface UIMachine {
  machine_resource_id: string
  name: string
  code: string
  setup_time_minutes: number
}

// Adapter functions  
function dbSetupTimeToUI(db: DatabaseSetupTime): SetupTime {
  // The database doesn't have these UI fields, so we add defaults
  return {
    ...db,
    notes: null, // Not in database
    requires_tool_change: false, // Not in database
    requires_material_change: false, // Not in database
    requires_cleaning: false, // Not in database
    is_sequence_dependent: false, // Not in database
    created_at: db.created_at || new Date().toISOString()
  }
}

function dbTaskToUI(task: DatabaseOptimizedTask & { job_optimized_patterns?: any }): UIOptimizedTask {
  return {
    optimized_task_id: task.optimized_task_id,
    task_name: task.name,
    pattern_name: task.job_optimized_patterns?.name || 'Unknown Pattern',
    pattern_id: task.pattern_id
  }
}

function dbMachineToUI(machine: DatabaseMachine): UIMachine {
  return {
    machine_resource_id: machine.machine_resource_id,
    name: machine.name,
    code: `M-${machine.machine_resource_id.slice(-6)}`,
    setup_time_minutes: machine.setup_time_minutes || 0
  }
}

const sampleSetupTimeData = [
  {
    from_optimized_task_id: "task_001",
    to_optimized_task_id: "task_002",
    machine_resource_id: "machine_001",
    setup_time_minutes: 30,
    notes: "Tool change required for different part dimensions",
    requires_tool_change: true,
    requires_material_change: false,
    requires_cleaning: false,
    is_sequence_dependent: false
  }
]

export default function SetupTimeFormRefactored() {
  const [editingSetupTime, setEditingSetupTime] = useState<DatabaseSetupTime | null>(null)
  const [activeTab, setActiveTab] = useState('list')

  // Use performance tracking hook
  const { 
    trackInteraction, 
    trackFieldFocus, 
    trackError 
  } = useFormPerformance('SetupTimeForm')

  // Use data fetching hooks
  const { 
    data: setupTimes, 
    loading: setupTimesLoading, 
    refresh: refreshSetupTimes 
  } = useFormData({
    fetchFn: async () => {
      const response = await optimizedTaskSetupTimeService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch setup times')
      }
      return response.data || []
    }
  })

  const { data, loading } = useMultipleFormData({
    optimizedTasks: async () => {
      const response = await optimizedTaskService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch tasks')
      }
      return response.data || []
    },
    machines: async () => {
      const response = await machineService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch machines')
      }
      return response.data || []
    }
  })

  const optimizedTasks = data.optimizedTasks || []
  const machines = data.machines || []

  // This is now handled later with uiGroupedTasks

  // Form setup
  const form = useForm<SetupTimeFormData>({
    defaultValues: {
      from_optimized_task_id: '',
      to_optimized_task_id: '',
      machine_resource_id: '',
      setup_time_minutes: 30,
      setup_type: 'standard',
      complexity_level: 'medium',
      requires_operator_skill: '',
      requires_certification: false,
      requires_supervisor_approval: false,
      setup_cost: 0,
      efficiency_impact_percent: 0,
      product_family_from: '',
      product_family_to: ''
    }
  })

  // Use form submission hook
  const { handleSubmit: submitForm, submitting } = useFormSubmission({
    onSubmit: async (data: SetupTimeFormData) => {
      if (editingSetupTime) {
        return await optimizedTaskSetupTimeService.update(editingSetupTime.setup_time_id, data)
      } else {
        return await optimizedTaskSetupTimeService.create(data)
      }
    },
    onSuccess: () => {
      form.reset()
      setEditingSetupTime(null)
      setActiveTab('list')
      refreshSetupTimes()
    },
    onError: trackError,
    successMessage: editingSetupTime ? "Setup time updated successfully" : "Setup time created successfully",
    formName: 'SetupTimeForm'
  })

  const handleEdit = (setupTime: SetupTime) => {
    // Find original database setup time
    const dbSetupTime = setupTimes?.find(st => st.setup_time_id === setupTime.setup_time_id)
    if (dbSetupTime) {
      setEditingSetupTime(dbSetupTime)
      form.reset({
        from_optimized_task_id: dbSetupTime.from_optimized_task_id,
        to_optimized_task_id: dbSetupTime.to_optimized_task_id,
        machine_resource_id: dbSetupTime.machine_resource_id,
        setup_time_minutes: dbSetupTime.setup_time_minutes,
        setup_type: dbSetupTime.setup_type,
        complexity_level: dbSetupTime.complexity_level,
        requires_operator_skill: dbSetupTime.requires_operator_skill || '',
        requires_certification: dbSetupTime.requires_certification,
        requires_supervisor_approval: dbSetupTime.requires_supervisor_approval,
        setup_cost: dbSetupTime.setup_cost,
        efficiency_impact_percent: dbSetupTime.efficiency_impact_percent,
        product_family_from: dbSetupTime.product_family_from || '',
        product_family_to: dbSetupTime.product_family_to || ''
      })
      setActiveTab('create')
      trackInteraction()
    }
  }

  const handleDelete = async (setupTimeId: string) => {
    if (confirm('Are you sure you want to delete this setup time?')) {
      try {
        const response = await optimizedTaskSetupTimeService.delete(setupTimeId)
        if (!response.success) {
          throw new Error(response.error || 'Failed to delete setup time')
        }
        refreshSetupTimes()
      } catch (error) {
        trackError()
      }
    }
    trackInteraction()
  }

  const handleCancel = () => {
    form.reset()
    setEditingSetupTime(null)
    setActiveTab('list')
    trackInteraction()
  }

  const isLoading = setupTimesLoading || loading.optimizedTasks || loading.machines
  
  // Transform data for UI components
  const uiSetupTimes = (setupTimes || []).map(dbSetupTimeToUI)
  const uiOptimizedTasks = (optimizedTasks || []).map(dbTaskToUI)
  const uiMachines = (machines || []).map(dbMachineToUI)
  
  // Group UI tasks by pattern
  const uiGroupedTasks = useMemo(() => {
    const grouped: Record<string, UIOptimizedTask[]> = {}
    uiOptimizedTasks.forEach(task => {
      const patternName = task.pattern_name
      if (!grouped[patternName]) {
        grouped[patternName] = []
      }
      grouped[patternName].push(task)
    })
    return grouped
  }, [uiOptimizedTasks])

  return (
    <FormLayout
      title="Setup Time Management"
      description="Define machine setup times between different tasks"
      loading={isLoading}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      tabs={[
        {
          value: 'list',
          label: 'View Setup Times',
          content: (
            <SetupTimesTable
              setupTimes={uiSetupTimes}
              optimizedTasks={uiOptimizedTasks}
              machines={uiMachines}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          )
        },
        {
          value: 'create',
          label: editingSetupTime ? 'Edit Setup Time' : 'Create Setup Time',
          content: (
            <form onSubmit={form.handleSubmit(submitForm)} noValidate>
              <SetupTimeFormFields
                form={form}
                optimizedTasks={uiOptimizedTasks}
                machines={uiMachines}
                groupedTasks={uiGroupedTasks}
                onFieldFocus={trackFieldFocus}
                onInteraction={trackInteraction}
              />

              <div className="flex gap-3 mt-6">
                <Button
                  type="submit"
                  disabled={submitting}
                  aria-busy={submitting}
                >
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {editingSetupTime ? 'Update' : 'Create'} Setup Time
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleCancel}
                  disabled={submitting}
                >
                  Cancel
                </Button>
              </div>
            </form>
          )
        },
        {
          value: 'bulk',
          label: 'Bulk Upload',
          content: (
            <MassUploader
              tableName="optimized_task_setup_times"
              entityName="Setup Time"
              sampleData={sampleSetupTimeData}
              onUploadComplete={refreshSetupTimes}
              requiredFields={['from_optimized_task_id', 'to_optimized_task_id', 'machine_resource_id', 'setup_time_minutes']}
              fieldDescriptions={{
                from_optimized_task_id: 'Source task ID',
                to_optimized_task_id: 'Target task ID',
                machine_resource_id: 'Machine ID (required)',
                setup_time_minutes: 'Setup time in minutes',
                notes: 'Optional notes or instructions',
                requires_tool_change: 'true or false (default: false)',
                requires_material_change: 'true or false (default: false)',
                requires_cleaning: 'true or false (default: false)',
                is_sequence_dependent: 'true or false (default: false)'
              }}
            />
          )
        }
      ]}
    />
  )
}