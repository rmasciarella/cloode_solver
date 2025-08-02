"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { machineService, departmentService } from '@/lib/services'
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'
import { MassUploader } from '@/components/ui/mass-uploader'
import { FormLayout } from '@/components/forms/common/FormLayout'
import { 
  useFormPerformance, 
  useFormData, 
  useFormSubmission 
} from '@/hooks/forms'
import { MachineFormFieldsRefactored } from './MachineFormFieldsRefactored'
import { MachinesTable } from './MachinesTable'
import { Database } from '@/lib/database.types'

// Use the database type
type DatabaseMachine = Database['public']['Tables']['machines']['Row']

// UI Machine type that includes additional fields for display
interface UIMachine extends DatabaseMachine {
  code: string
  description: string | null
  capacity_per_hour: number
  hourly_operating_cost: number
  requires_skilled_operator: boolean
  department?: { name: string | undefined; code: string }
}

// Adapter function to convert database machine to UI machine
function databaseMachineToUI(dbMachine: DatabaseMachine): UIMachine {
  return {
    ...dbMachine,
    code: `M-${dbMachine.machine_resource_id.slice(-6)}`, // Generate a code from ID
    description: null, // Not in database
    capacity_per_hour: dbMachine.capacity,
    hourly_operating_cost: dbMachine.cost_per_hour,
    requires_skilled_operator: false, // Default value since not in database
    department: undefined // Will be added separately if needed
  }
}

interface MachineFormData {
  name: string
  capacity: number  // Changed from capacity_per_hour
  cost_per_hour: number  // Changed from hourly_operating_cost
  department_id: string
  cell_id: string
  setup_time_minutes: number
  teardown_time_minutes: number
  maintenance_interval_hours: number
  machine_type: string
  is_active: boolean
  // Additional fields for user convenience (not in database)
  code?: string | undefined
  description?: string | undefined
  requires_skilled_operator?: boolean | undefined
}

const sampleMachineData = [
  {
    name: "CNC Mill 1",
    capacity: 10,  // Changed from capacity_per_hour
    cost_per_hour: 85.50,  // Changed from hourly_operating_cost
    department_id: "dept_123",
    cell_id: "cell_123",
    setup_time_minutes: 30,
    teardown_time_minutes: 15,  // Added required field
    maintenance_interval_hours: 200,
    machine_type: "cnc",
    is_active: true,
    // Optional fields for UI
    code: "CNC-001",
    description: "High precision 5-axis CNC milling machine",
    requires_skilled_operator: true
  }
]

export default function MachineFormRefactored() {
  const [editingMachine, setEditingMachine] = useState<DatabaseMachine | null>(null)
  const [activeTab, setActiveTab] = useState('list')

  // Use performance tracking hook
  const { 
    trackInteraction, 
    trackFieldFocus, 
    trackError 
  } = useFormPerformance('MachineForm')

  // Use data fetching hooks
  const { 
    data: machines, 
    loading: machinesLoading, 
    refresh: refreshMachines 
  } = useFormData({
    fetchFn: async () => {
      const response = await machineService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch machines')
      }
      return response.data || []
    }
  })

  const { 
    data: departments, 
    loading: departmentsLoading 
  } = useFormData({
    fetchFn: async () => {
      const response = await departmentService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch departments')
      }
      return response.data || []
    }
  })

  // Form setup
  const form = useForm<MachineFormData>({
    defaultValues: {
      name: '',
      capacity: 1,  // Default capacity
      cost_per_hour: 0,
      department_id: '',
      cell_id: '',
      setup_time_minutes: 0,
      teardown_time_minutes: 0,
      maintenance_interval_hours: 0,
      machine_type: '',
      is_active: true,
      // Optional UI fields
      code: '',
      description: '',
      requires_skilled_operator: false
    }
  })

  // Use form submission hook
  const { handleSubmit: submitForm, submitting } = useFormSubmission({
    onSubmit: async (data: MachineFormData) => {
      // Map form data to database format
      const dbData = {
        name: data.name,
        capacity: data.capacity,
        cost_per_hour: data.cost_per_hour,
        department_id: data.department_id || null,
        cell_id: data.cell_id,
        setup_time_minutes: data.setup_time_minutes,
        teardown_time_minutes: data.teardown_time_minutes,
        maintenance_interval_hours: data.maintenance_interval_hours,
        machine_type: data.machine_type || null,
        is_active: data.is_active
        // Note: code, description, requires_skilled_operator are UI-only fields
      }
      
      if (editingMachine) {
        return await machineService.update(editingMachine.machine_resource_id, dbData)
      } else {
        return await machineService.create(dbData)
      }
    },
    onSuccess: () => {
      form.reset()
      setEditingMachine(null)
      setActiveTab('list')
      refreshMachines()
    },
    onError: trackError,
    successMessage: editingMachine ? "Machine updated successfully" : "Machine created successfully",
    formName: 'MachineForm'
  })

  const handleEdit = (machine: UIMachine) => {
    // Find the original database machine
    const dbMachine = machines?.find(m => m.machine_resource_id === machine.machine_resource_id)
    if (dbMachine) {
      setEditingMachine(dbMachine)
      form.reset({
        name: dbMachine.name,
        capacity: dbMachine.capacity,
        cost_per_hour: dbMachine.cost_per_hour,
        department_id: dbMachine.department_id || '',
        cell_id: dbMachine.cell_id,
        setup_time_minutes: dbMachine.setup_time_minutes,
        teardown_time_minutes: dbMachine.teardown_time_minutes,
        maintenance_interval_hours: dbMachine.maintenance_interval_hours,
        machine_type: dbMachine.machine_type || '',
        is_active: dbMachine.is_active,
        // Optional UI fields
        code: machine.code,  // Use the generated code
        description: machine.description || '',
        requires_skilled_operator: machine.requires_skilled_operator
      })
      setActiveTab('create')
      trackInteraction()
    }
  }

  const handleDelete = async (machineId: string) => {
    if (confirm('Are you sure you want to delete this machine?')) {
      try {
        const response = await machineService.delete(machineId)
        if (!response.success) {
          throw new Error(response.error || 'Failed to delete machine')
        }
        refreshMachines()
      } catch (error) {
        trackError()
      }
    }
    trackInteraction()
  }

  const handleCancel = () => {
    form.reset()
    setEditingMachine(null)
    setActiveTab('list')
    trackInteraction()
  }

  const loading = machinesLoading || departmentsLoading
  
  // Transform database machines to UI machines
  const uiMachines = (machines || []).map(m => databaseMachineToUI(m))

  return (
    <FormLayout
      title="Machine Management"
      description="Configure and manage production machines and equipment"
      loading={loading}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      tabs={[
        {
          value: 'list',
          label: 'View Machines',
          content: (
            <MachinesTable
              machines={uiMachines}
              departments={departments}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          )
        },
        {
          value: 'create',
          label: editingMachine ? 'Edit Machine' : 'Create Machine',
          content: (
            <form onSubmit={form.handleSubmit(submitForm)} noValidate>
              <MachineFormFieldsRefactored
                form={form}
                departments={departments || []}
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
                  {editingMachine ? 'Update' : 'Create'} Machine
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
              tableName="machines"
              entityName="Machine"
              sampleData={sampleMachineData}
              onUploadComplete={refreshMachines}
              requiredFields={['name', 'capacity', 'cost_per_hour', 'cell_id', 'setup_time_minutes', 'teardown_time_minutes', 'maintenance_interval_hours']}
              fieldDescriptions={{
                name: 'Machine name',
                capacity: 'Production capacity (units per hour)',
                cost_per_hour: 'Operating cost per hour',
                department_id: 'ID of the department (optional)',
                cell_id: 'Work cell ID (required)',
                setup_time_minutes: 'Setup/changeover time in minutes',
                teardown_time_minutes: 'Teardown time in minutes',
                maintenance_interval_hours: 'Hours between maintenance',
                machine_type: 'One of: cnc, laser, welding, assembly, packaging, testing, other',
                is_active: 'true or false (default: true)'
              }}
            />
          )
        }
      ]}
    />
  )
}