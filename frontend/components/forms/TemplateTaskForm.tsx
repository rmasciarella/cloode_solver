"use client"

import { useTemplateTaskData } from './template-tasks/useTemplateTaskData'
import { useTemplateTaskForm } from './template-tasks/useTemplateTaskForm'
import { TemplateTaskFormFields } from './template-tasks/TemplateTaskFormFields'
import { TemplateTasksTable } from './template-tasks/TemplateTasksTable'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MassUploader } from '@/components/ui/mass-uploader'

type OptimizedTask = {
  optimized_task_id: string
  pattern_id: string
  name: string
  position: number
  department_id: string | null
  is_unattended: boolean
  is_setup: boolean
  sequence_id: string | null
  min_operators: number
  max_operators: number
  operator_efficiency_curve: string | null
  created_at: string
}

type JobOptimizedPattern = {
  pattern_id: string
  name: string
}

type Department = {
  department_id: string
  name: string
  code: string
}

type SequenceResource = {
  sequence_id: string
  name: string
}

type OptimizedTaskFormData = {
  pattern_id: string
  name: string
  position: number
  department_id: string
  is_unattended: boolean
  is_setup: boolean
  sequence_id: string
  min_operators: number
  max_operators: number
  operator_efficiency_curve: string
}

const efficiencyCurves = [
  { value: 'linear', label: 'Linear' },
  { value: 'exponential', label: 'Exponential' },
  { value: 'logarithmic', label: 'Logarithmic' },
  { value: 'plateau', label: 'Plateau' }
]

export default function OptimizedTaskForm() {
  const {
    optimizedTasks,
    jobOptimizedPatterns,
    departments,
    sequenceResources,
    loading,
    fetchOptimizedTasks
  } = useTemplateTaskData()

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    errors,
    editingId,
    isSubmitting,
    onSubmit,
    handleEdit,
    handleDelete,
    handleCancel
  } = useTemplateTaskForm(fetchOptimizedTasks)

  const fetchOptimizedTasks = async () => {
    setLoading(true)
    try {
      const response = await optimizedTaskService.getAllWithPatterns()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch optimized tasks')
      }
      setOptimizedTasks(response.data || [])
    } catch (error) {
      console.error('Error fetching optimized tasks:', error)
      toast({
        title: "Error",
        description: "Failed to fetch optimized tasks",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchJobOptimizedPatterns = async () => {
    try {
      const response = await jobTemplateService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch job optimized patterns')
      }
      setJobOptimizedPatterns(response.data || [])
    } catch (error) {
      console.error('Error fetching job optimized patterns:', error)
    }
  }

  const fetchDepartments = async () => {
    try {
      const response = await departmentService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch departments')
      }
      setDepartments(response.data || [])
    } catch (error) {
      console.error('Error fetching departments:', error)
    }
  }

  const fetchSequenceResources = async () => {
    try {
      const response = await sequenceResourceService.getAll()
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch sequence resources')
      }
      setSequenceResources(response.data || [])
    } catch (error) {
      console.error('Error fetching sequence resources:', error)
    }
  }

  useEffect(() => {
    fetchOptimizedTasks()
    fetchJobOptimizedPatterns()
    fetchDepartments()
    fetchSequenceResources()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const onSubmit = async (data: OptimizedTaskFormData) => {
    setIsSubmitting(true)
    try {
      const formData = {
        pattern_id: data.pattern_id,
        name: data.name,
        position: data.position,
        department_id: data.department_id || null,
        is_unattended: data.is_unattended,
        is_setup: data.is_setup,
        sequence_id: data.sequence_id || null,
        min_operators: data.min_operators,
        max_operators: data.max_operators,
        operator_efficiency_curve: data.operator_efficiency_curve || null
      }

      if (editingId) {
        const response = await optimizedTaskService.update(editingId, formData)

        if (!response.success) {
          throw new Error(response.error || 'Failed to update optimized task')
        }

        toast({
          title: "Success",
          description: "Optimized task updated successfully"
        })
      } else {
        const response = await optimizedTaskService.create(formData)

        if (!response.success) {
          throw new Error(response.error || 'Failed to create optimized task')
        }

        toast({
          title: "Success",
          description: "Optimized task created successfully"
        })
      }

      reset()
      setEditingId(null)
      fetchOptimizedTasks()
    } catch (error) {
      console.error('Error saving optimized task:', error)
      toast({
        title: "Error",
        description: "Failed to save optimized task",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = (task: OptimizedTask) => {
    setEditingId(task.optimized_task_id)
    setValue('pattern_id', task.pattern_id)
    setValue('name', task.name)
    setValue('position', task.position)
    setValue('department_id', task.department_id || '')
    setValue('is_unattended', task.is_unattended)
    setValue('is_setup', task.is_setup)
    setValue('sequence_id', task.sequence_id || '')
    setValue('operator_efficiency_curve', task.operator_efficiency_curve || 'linear')
    setValue('min_operators', task.min_operators)
    setValue('max_operators', task.max_operators)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this optimized task?')) return

    try {
      const response = await optimizedTaskService.delete(id)

      if (!response.success) {
        throw new Error(response.error || 'Failed to delete optimized task')
      }

      toast({
        title: "Success",
        description: "Optimized task deleted successfully"
      })
      fetchOptimizedTasks()
    } catch (error) {
      console.error('Error deleting optimized task:', error)
      toast({
        title: "Error",
        description: "Failed to delete optimized task",
        variant: "destructive"
      })
    }
  }

  const handleCancel = () => {
    reset()
    setEditingId(null)
  }

  const sampleTemplateTaskData = {
    pattern_id: '',
    name: 'Assembly Step 1',
    position: 1,
    department_id: null,
    is_unattended: false,
    is_setup: false,
    sequence_id: null,
    min_operators: 1,
    max_operators: 2,
    operator_efficiency_curve: 'linear'
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="form" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="form">Single Entry</TabsTrigger>
          <TabsTrigger value="bulk">Mass Upload</TabsTrigger>
        </TabsList>
        
        <TabsContent value="form" className="space-y-6">
          {/* Form Card */}
          <Card>
        <CardHeader>
          <CardTitle>{editingId ? 'Edit Optimized Task' : 'Create New Optimized Task'}</CardTitle>
          <CardDescription>
            {editingId ? 'Update optimized task information' : 'Add a new task to a job optimized pattern'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Template - Required */}
              <div className="space-y-2">
                <Label htmlFor="pattern_id">Job Optimized Pattern *</Label>
                <Select onValueChange={(value) => setValue('pattern_id', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select job optimized pattern" />
                  </SelectTrigger>
                  <SelectContent>
                    {jobOptimizedPatterns.map((pattern) => (
                      <SelectItem key={pattern.pattern_id} value={pattern.pattern_id}>
                        {pattern.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {!watch('pattern_id') && <p className="text-sm text-red-600">Job optimized pattern is required</p>}
              </div>

              {/* Name - Required */}
              <div className="space-y-2">
                <Label htmlFor="name">Task Name *</Label>
                <Input
                  id="name"
                  {...register('name', { 
                    required: 'Task name is required',
                    maxLength: { value: 255, message: 'Name must be 255 characters or less' }
                  })}
                  placeholder="e.g., Assembly Step 1"
                />
                {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
              </div>

              {/* Position - Required */}
              <div className="space-y-2">
                <Label htmlFor="position">Position *</Label>
                <Input
                  id="position"
                  type="number"
                  min="1"
                  {...register('position', { 
                    valueAsNumber: true,
                    required: 'Position is required',
                    min: { value: 1, message: 'Position must be at least 1' }
                  })}
                />
                {errors.position && <p className="text-sm text-red-600">{errors.position.message}</p>}
              </div>

              {/* Department - Required */}
              <div className="space-y-2">
                <Label htmlFor="department_id">Department *</Label>
                <Select onValueChange={(value) => setValue('department_id', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select department" />
                  </SelectTrigger>
                  <SelectContent>
                    {departments.map((dept) => (
                      <SelectItem key={dept.department_id} value={dept.department_id}>
                        {dept.name} ({dept.code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {!watch('department_id') && <p className="text-sm text-red-600">Department is required</p>}
              </div>


              {/* Sequence Resource */}
              <div className="space-y-2">
                <Label htmlFor="sequence_id">Sequence Resource</Label>
                <Select onValueChange={(value) => setValue('sequence_id', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select sequence resource" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No Sequence Resource</SelectItem>
                    {sequenceResources.map((resource) => (
                      <SelectItem key={resource.sequence_id} value={resource.sequence_id}>
                        {resource.name} ({resource.sequence_id})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>


              {/* Minimum Operators */}
              <div className="space-y-2">
                <Label htmlFor="min_operators">Minimum Operators</Label>
                <Input
                  id="min_operators"
                  type="number"
                  min="1"
                  {...register('min_operators', { 
                    valueAsNumber: true,
                    min: { value: 1, message: 'Must have at least 1 operator' }
                  })}
                />
                {errors.min_operators && <p className="text-sm text-red-600">{errors.min_operators.message}</p>}
              </div>

              {/* Maximum Operators */}
              <div className="space-y-2">
                <Label htmlFor="max_operators">Maximum Operators</Label>
                <Input
                  id="max_operators"
                  type="number"
                  min="1"
                  {...register('max_operators', { 
                    valueAsNumber: true,
                    min: { value: 1, message: 'Must have at least 1 operator' },
                    validate: (value) => {
                      const minOps = watch('min_operators') || 1
                      return value >= minOps || 'Maximum must be >= minimum operators'
                    }
                  })}
                />
                {errors.max_operators && <p className="text-sm text-red-600">{errors.max_operators.message}</p>}
              </div>
            </div>

            {/* Checkboxes */}
            <div className="flex flex-col space-y-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_unattended"
                  checked={watch('is_unattended')}
                  onCheckedChange={(checked) => setValue('is_unattended', checked as boolean)}
                />
                <Label htmlFor="is_unattended">Unattended Operation</Label>
                <p className="text-xs text-gray-500 ml-2">Task can run without operator supervision</p>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_setup"
                  checked={watch('is_setup')}
                  onCheckedChange={(checked) => setValue('is_setup', checked as boolean)}
                />
                <Label htmlFor="is_setup">Setup Task</Label>
                <p className="text-xs text-gray-500 ml-2">This is a setup or preparation task</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="operator_efficiency_curve">Operator Efficiency Curve</Label>
                <Select value={watch('operator_efficiency_curve')} onValueChange={(value) => setValue('operator_efficiency_curve', value)}>
                  <SelectTrigger id="operator_efficiency_curve">
                    <SelectValue placeholder="Select efficiency curve" />
                  </SelectTrigger>
                  <SelectContent>
                    {efficiencyCurves.map((curve) => (
                      <SelectItem key={curve.value} value={curve.value}>
                        {curve.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500">How operator efficiency changes with experience</p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-2 pt-4">
              {editingId && (
                <Button type="button" variant="outline" onClick={handleCancel}>
                  Cancel
                </Button>
              )}
              <Button type="submit" disabled={isSubmitting || !watch('pattern_id') || !watch('department_id')}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {editingId ? 'Update' : 'Create'} Task
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
        </TabsContent>
        
        <TabsContent value="bulk" className="space-y-6">
          <MassUploader
            tableName="optimized_tasks"
            entityName="Template Task"
            sampleData={sampleTemplateTaskData}
            onUploadComplete={fetchOptimizedTasks}
            requiredFields={['pattern_id', 'name', 'position']}
            fieldDescriptions={{
              pattern_id: 'Job optimized pattern ID (required)',
              name: 'Task display name',
              position: 'Task position in sequence (integer)',
              department_id: 'Department ID where task is performed',
              min_operators: 'Minimum operators required (default: 1)',
              max_operators: 'Maximum operators that can work (default: 1)',
              is_unattended: 'Can run without supervision (true/false)',
              is_setup: 'Is a setup/preparation task (true/false)',
              operator_efficiency_curve: 'linear, exponential, logarithmic, plateau'
            }}
          />
        </TabsContent>
      </Tabs>

      {/* Template Tasks List */}
      <Card>
        <CardHeader>
          <CardTitle>Optimized Tasks</CardTitle>
          <CardDescription>Manage existing optimized tasks</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : optimizedTasks.length === 0 ? (
            <p className="text-center text-gray-500 py-4">No optimized tasks found</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Position</th>
                    <th className="text-left p-2">Task Name</th>
                    <th className="text-left p-2">Pattern</th>
                    <th className="text-left p-2">Department</th>
                    <th className="text-left p-2">Operators</th>
                    <th className="text-left p-2">Efficiency Curve</th>
                    <th className="text-left p-2">Flags</th>
                    <th className="text-left p-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {optimizedTasks.map((task: any) => {
                    const department = departments.find(d => d.department_id === task.department_id)
                    return (
                      <tr key={task.optimized_task_id} className="border-b hover:bg-gray-50">
                        <td className="p-2 font-medium">{task.position}</td>
                        <td className="p-2">{task.name}</td>
                        <td className="p-2">{task.job_optimized_patterns?.name || 'Unknown'}</td>
                        <td className="p-2">{department ? `${department.name} (${department.code})` : '-'}</td>
                        <td className="p-2">{task.min_operators}-{task.max_operators}</td>
                        <td className="p-2">
                          <span className="capitalize">{task.operator_efficiency_curve || 'linear'}</span>
                        </td>
                        <td className="p-2">
                          <div className="flex flex-wrap gap-1">
                            {task.is_setup && (
                              <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">Setup</span>
                            )}
                            {task.is_unattended && (
                              <span className="px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">Unattended</span>
                            )}
                          </div>
                        </td>
                        <td className="p-2">
                          <div className="flex space-x-1">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleEdit(task)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDelete(task.optimized_task_id)}
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