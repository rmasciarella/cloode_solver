"use client"

import { useState, useEffect, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { supabase } from '@/lib/supabase'
import { useToast } from '@/hooks/use-toast'
import { useFormPerformance } from '@/lib/hooks/use-form-performance'
import { handleFormError, logUnmappedError } from '@/lib/utils/error-mapping'
import { PerformanceDebugPanel } from '@/components/ui/performance-debug-panel'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MassUploader } from '@/components/ui/mass-uploader'
import { Loader2, Edit, Trash2, Upload } from 'lucide-react'

type JobTask = {
  task_id: string
  instance_id: string
  template_task_id: string
  selected_mode_id: string | null
  assigned_machine_id: string | null
  start_time_minutes: number | null
  end_time_minutes: number | null
  actual_duration_minutes: number | null
  setup_time_minutes: number
  created_at: string
}

type JobInstance = {
  instance_id: string
  name: string
  template_id: string
}

type TemplateTask = {
  template_task_id: string
  name: string
  template_id: string
}

type TemplateTaskMode = {
  template_task_mode_id: string
  mode_name: string
  duration_minutes: number
}

type Machine = {
  machine_resource_id: string
  name: string
}

type JobTaskFormData = {
  instance_id: string
  template_task_id: string
  selected_mode_id: string
  assigned_machine_id: string
  start_time_minutes: number
  end_time_minutes: number
  actual_duration_minutes: number
  setup_time_minutes: number
}


const sampleJobTaskData = {
  instance_id: "JOB_001",
  template_task_id: "TASK_001", 
  selected_mode_id: "MODE_001",
  assigned_machine_id: "MACHINE_001",
  start_time_minutes: 0,
  end_time_minutes: 60,
  actual_duration_minutes: 55,
  setup_time_minutes: 5
}

export default function JobTaskForm() {
  const [jobTasks, setJobTasks] = useState<JobTask[]>([])
  const [jobInstances, setJobInstances] = useState<JobInstance[]>([])
  const [templateTasks, setTemplateTasks] = useState<TemplateTask[]>([])
  const [taskModes, setTaskModes] = useState<TemplateTaskMode[]>([])
  const [machines, setMachines] = useState<Machine[]>([])
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()
  
  // Performance monitoring with standardized hook
  const performanceTracker = useFormPerformance('job-task-form')

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<JobTaskFormData>({
    defaultValues: {
      instance_id: '',
      template_task_id: '',
      selected_mode_id: '',
      assigned_machine_id: '',
      start_time_minutes: 0,
      end_time_minutes: 0,
      actual_duration_minutes: 0,
      setup_time_minutes: 0
    }
  })

  // Enhanced register function with performance tracking
  const registerWithPerformance = useCallback((name: keyof JobTaskFormData, validation?: any) => {
    return {
      ...register(name, validation),
      onFocus: (e: any) => {
        performanceTracker.trackInteraction('focus', name)
        // React Hook Form doesn't provide onFocus, handle manually
      },
      onBlur: (e: any) => {
        // Track field validation
        performanceTracker.startValidation(name)
        
        // Let react-hook-form handle validation
        const hasError = !!errors[name]
        performanceTracker.trackValidation(name, hasError)
        
        // Call original onBlur if it exists
        register(name, validation).onBlur?.(e)
      },
      onChange: (e: any) => {
        performanceTracker.trackInteraction('change', name)
        register(name, validation).onChange?.(e)
      }
    }
  }, [register, performanceTracker, errors])

  const fetchJobTasks = async () => {
    setLoading(true)
    try {
      const { data, error } = await supabase
        .from('job_tasks')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(10)

      if (error) throw error
      setJobTasks(data || [])
    } catch (error) {
      console.error('Error fetching job tasks:', error)
      logUnmappedError(error, 'fetchJobTasks')
      const errorInfo = handleFormError(error, 'job tasks', 'fetch')
      toast(errorInfo)
    } finally {
      setLoading(false)
    }
  }

  const fetchJobInstances = async () => {
    try {
      const { data, error } = await supabase
        .from('job_instances')
        .select('instance_id, name, template_id')
        .order('name', { ascending: true })

      if (error) throw error
      setJobInstances(data || [])
    } catch (error) {
      console.error('Error fetching job instances:', error)
    }
  }

  const fetchTemplateTasks = async () => {
    try {
      const { data, error } = await supabase
        .from('template_tasks')
        .select('template_task_id, name, template_id')
        .order('name', { ascending: true })

      if (error) throw error
      setTemplateTasks(data || [])
    } catch (error) {
      console.error('Error fetching template tasks:', error)
    }
  }

  const fetchTaskModes = async () => {
    try {
      const { data, error } = await supabase
        .from('template_task_modes')
        .select('template_task_mode_id, mode_name, duration_minutes, template_task_id')
        .order('mode_name', { ascending: true })

      if (error) throw error
      setTaskModes(data || [])
    } catch (error) {
      console.error('Error fetching task modes:', error)
    }
  }

  const fetchMachines = async () => {
    try {
      const { data, error } = await supabase
        .from('machines')
        .select('machine_resource_id, name')
        .eq('is_active', true)
        .order('name', { ascending: true })

      if (error) throw error
      setMachines(data || [])
    } catch (error) {
      console.error('Error fetching machines:', error)
    }
  }

  useEffect(() => {
    fetchJobTasks()
    fetchJobInstances()
    fetchTemplateTasks()
    fetchTaskModes()
    fetchMachines()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const onSubmit = async (data: JobTaskFormData) => {
    setIsSubmitting(true)
    performanceTracker.trackSubmissionStart()
    
    try {
      // Validate business logic
      performanceTracker.startValidation('time_validation')
      if (data.start_time_minutes >= data.end_time_minutes) {
        performanceTracker.trackValidation('time_validation', true, 'End time must be after start time')
        toast({
          title: "Error",
          description: "End time must be after start time",
          variant: "destructive"
        })
        performanceTracker.trackSubmissionEnd(false)
        setIsSubmitting(false)
        return
      }
      performanceTracker.trackValidation('time_validation', false)

      const formData = {
        instance_id: data.instance_id,
        template_task_id: data.template_task_id,
        selected_mode_id: data.selected_mode_id || null,
        assigned_machine_id: data.assigned_machine_id || null,
        start_time_minutes: data.start_time_minutes || null,
        end_time_minutes: data.end_time_minutes || null,
        actual_duration_minutes: data.actual_duration_minutes || null,
        setup_time_minutes: data.setup_time_minutes
      }

      if (editingId) {
        const { error } = await supabase
          .from('job_tasks')
          .update(formData)
          .eq('task_id', editingId)

        if (error) throw error

        toast({
          title: "Success",
          description: "Job task updated successfully"
        })
      } else {
        const { error } = await supabase
          .from('job_tasks')
          .insert([formData])

        if (error) throw error

        toast({
          title: "Success",
          description: "Job task created successfully"
        })
      }

      reset()
      setEditingId(null)
      fetchJobTasks()
      performanceTracker.trackSubmissionEnd(true)
    } catch (error) {
      console.error('Error saving job task:', error)
      logUnmappedError(error, 'saveJobTask')
      performanceTracker.trackSubmissionEnd(false)
      const errorInfo = handleFormError(error, 'job task', editingId ? 'update' : 'create')
      toast(errorInfo)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = (task: JobTask) => {
    setEditingId(task.task_id)
    setValue('instance_id', task.instance_id)
    setValue('template_task_id', task.template_task_id)
    setValue('selected_mode_id', task.selected_mode_id || '')
    setValue('assigned_machine_id', task.assigned_machine_id || '')
    setValue('start_time_minutes', task.start_time_minutes || 0)
    setValue('end_time_minutes', task.end_time_minutes || 0)
    setValue('actual_duration_minutes', task.actual_duration_minutes || 0)
    setValue('setup_time_minutes', task.setup_time_minutes)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this job task assignment?')) return

    try {
      const { error } = await supabase
        .from('job_tasks')
        .delete()
        .eq('task_id', id)

      if (error) throw error

      toast({
        title: "Success",
        description: "Job task deleted successfully"
      })
      fetchJobTasks()
    } catch (error) {
      console.error('Error deleting job task:', error)
      logUnmappedError(error, 'deleteJobTask')
      const errorInfo = handleFormError(error, 'job task', 'delete')
      toast(errorInfo)
    }
  }

  const handleCancel = () => {
    reset()
    setEditingId(null)
  }

  const getFilteredTasks = (instanceId: string) => {
    const instance = jobInstances.find(inst => inst.instance_id === instanceId)
    if (!instance) return []
    
    return templateTasks.filter(task => task.template_id === instance.template_id)
  }

  const getFilteredModes = (taskId: string) => {
    return taskModes.filter(mode => (mode as any).template_task_id === taskId)
  }

  const selectedInstanceId = watch('instance_id')
  const selectedTaskId = watch('template_task_id')

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
          <CardTitle>{editingId ? 'Edit Job Task Assignment' : 'Create New Job Task Assignment'}</CardTitle>
          <CardDescription>
            {editingId ? 'Update job task assignment details' : 'Assign template tasks to job instances with timing and resource allocation'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Job Instance - Required */}
              <div className="space-y-2">
                <Label htmlFor="instance_id">Job Instance *</Label>
                <Select onValueChange={(value) => {
                  performanceTracker.startValidation('instance_id')
                  setValue('instance_id', value)
                  setValue('template_task_id', '')
                  setValue('selected_mode_id', '')
                  performanceTracker.trackInteraction('click', 'instance_id')
                  performanceTracker.trackValidation('instance_id', !value)
                }}>
                  <SelectTrigger
                    onFocus={() => performanceTracker.trackInteraction('focus', 'instance_id')}
                    onClick={() => performanceTracker.trackInteraction('click', 'instance_id')}
                  >
                    <SelectValue placeholder="Select job instance" />
                  </SelectTrigger>
                  <SelectContent>
                    {jobInstances.map((instance) => (
                      <SelectItem key={instance.instance_id} value={instance.instance_id}>
                        {instance.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {!watch('instance_id') && <p className="text-sm text-red-600">Job instance is required</p>}
              </div>

              {/* Template Task - Required */}
              <div className="space-y-2">
                <Label htmlFor="template_task_id">Template Task *</Label>
                <Select 
                  onValueChange={(value) => {
                    performanceTracker.startValidation('template_task_id')
                    setValue('template_task_id', value)
                    setValue('selected_mode_id', '')
                    performanceTracker.trackInteraction('click', 'template_task_id')
                    performanceTracker.trackValidation('template_task_id', !value)
                  }}
                  disabled={!selectedInstanceId}
                >
                  <SelectTrigger
                    onFocus={() => performanceTracker.trackInteraction('focus', 'template_task_id')}
                    onClick={() => performanceTracker.trackInteraction('click', 'template_task_id')}
                  >
                    <SelectValue placeholder="Select template task" />
                  </SelectTrigger>
                  <SelectContent>
                    {getFilteredTasks(selectedInstanceId).map((task) => (
                      <SelectItem key={task.template_task_id} value={task.template_task_id}>
                        {task.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {!watch('template_task_id') && selectedInstanceId && 
                  <p className="text-sm text-red-600">Template task is required</p>}
              </div>

              {/* Task Mode */}
              <div className="space-y-2">
                <Label htmlFor="selected_mode_id">Task Mode</Label>
                <Select 
                  onValueChange={(value) => setValue('selected_mode_id', value)}
                  disabled={!selectedTaskId}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select task mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No Specific Mode</SelectItem>
                    {getFilteredModes(selectedTaskId).map((mode) => (
                      <SelectItem key={mode.template_task_mode_id} value={mode.template_task_mode_id}>
                        {mode.mode_name} ({mode.duration_minutes}m)
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Assigned Machine */}
              <div className="space-y-2">
                <Label htmlFor="assigned_machine_id">Assigned Machine</Label>
                <Select onValueChange={(value) => setValue('assigned_machine_id', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select machine" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No Machine Assignment</SelectItem>
                    {machines.map((machine) => (
                      <SelectItem key={machine.machine_resource_id} value={machine.machine_resource_id}>
                        {machine.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Start Time Minutes */}
              <div className="space-y-2">
                <Label htmlFor="start_time_minutes">Start Time (minutes)</Label>
                <Input
                  id="start_time_minutes"
                  type="number"
                  min="0"
                  {...registerWithPerformance('start_time_minutes', { 
                    valueAsNumber: true,
                    min: { value: 0, message: 'Start time must be non-negative' }
                  })}
                />
                <p className="text-xs text-gray-500">Time from schedule start in minutes</p>
                {errors.start_time_minutes && <p className="text-sm text-red-600">{errors.start_time_minutes.message}</p>}
              </div>

              {/* End Time Minutes */}
              <div className="space-y-2">
                <Label htmlFor="end_time_minutes">End Time (minutes)</Label>
                <Input
                  id="end_time_minutes"
                  type="number"
                  min="0"
                  {...registerWithPerformance('end_time_minutes', { 
                    valueAsNumber: true,
                    min: { value: 0, message: 'End time must be non-negative' }
                  })}
                />
                <p className="text-xs text-gray-500">Task completion time in minutes</p>
                {errors.end_time_minutes && <p className="text-sm text-red-600">{errors.end_time_minutes.message}</p>}
              </div>

              {/* Actual Duration Minutes */}
              <div className="space-y-2">
                <Label htmlFor="actual_duration_minutes">Actual Duration (minutes)</Label>
                <Input
                  id="actual_duration_minutes"
                  type="number"
                  min="0"
                  {...registerWithPerformance('actual_duration_minutes', { 
                    valueAsNumber: true,
                    min: { value: 0, message: 'Duration must be non-negative' }
                  })}
                />
                <p className="text-xs text-gray-500">Actual time taken to complete task</p>
                {errors.actual_duration_minutes && <p className="text-sm text-red-600">{errors.actual_duration_minutes.message}</p>}
              </div>

              {/* Setup Time Minutes */}
              <div className="space-y-2">
                <Label htmlFor="setup_time_minutes">Setup Time (minutes)</Label>
                <Input
                  id="setup_time_minutes"
                  type="number"
                  min="0"
                  {...registerWithPerformance('setup_time_minutes', { 
                    valueAsNumber: true,
                    min: { value: 0, message: 'Setup time must be non-negative' }
                  })}
                />
                <p className="text-xs text-gray-500">Time required for task setup</p>
                {errors.setup_time_minutes && <p className="text-sm text-red-600">{errors.setup_time_minutes.message}</p>}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-2 pt-4">
              {editingId && (
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => {
                    performanceTracker.trackInteraction('click', 'cancel_button')
                    handleCancel()
                  }}
                >
                  Cancel
                </Button>
              )}
              <Button 
                type="submit" 
                disabled={isSubmitting || !watch('instance_id') || !watch('template_task_id')}
                onClick={() => performanceTracker.trackInteraction('click', 'submit_button')}
              >
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {editingId ? 'Update' : 'Create'} Job Task
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Job Tasks List */}
      <Card>
        <CardHeader>
          <CardTitle>Job Task Assignments</CardTitle>
          <CardDescription>Manage existing job task assignments and their execution details</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : jobTasks.length === 0 ? (
            <p className="text-center text-gray-500 py-4">No job tasks found</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Job Instance</th>
                    <th className="text-left p-2">Task</th>
                    <th className="text-left p-2">Mode</th>
                    <th className="text-left p-2">Machine</th>
                    <th className="text-left p-2">Start</th>
                    <th className="text-left p-2">End</th>
                    <th className="text-left p-2">Duration</th>
                    <th className="text-left p-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobTasks.map((task: any) => {
                    const instance = jobInstances.find(i => i.instance_id === task.instance_id)
                    const templateTask = templateTasks.find(t => t.template_task_id === task.template_task_id)
                    const taskMode = taskModes.find(m => m.template_task_mode_id === task.selected_mode_id)
                    const machine = machines.find(m => m.machine_resource_id === task.assigned_machine_id)
                    
                    return (
                      <tr key={task.task_id} className="border-b hover:bg-gray-50">
                        <td className="p-2 font-medium">{instance?.name || 'Unknown'}</td>
                        <td className="p-2">{templateTask?.name || 'Unknown'}</td>
                        <td className="p-2">
                          {taskMode?.mode_name || 'No mode'}
                          {taskMode?.duration_minutes && (
                            <div className="text-xs text-gray-500">
                              {taskMode.duration_minutes}m
                            </div>
                          )}
                        </td>
                        <td className="p-2">{machine?.name || 'Unassigned'}</td>
                        <td className="p-2">
                          {task.start_time_minutes !== null ? `${task.start_time_minutes}m` : '-'}
                        </td>
                        <td className="p-2">
                          {task.end_time_minutes !== null ? `${task.end_time_minutes}m` : '-'}
                        </td>
                        <td className="p-2">
                          {task.actual_duration_minutes !== null ? (
                            <span className="text-green-600">{task.actual_duration_minutes}m</span>
                          ) : (
                            <span className="text-gray-400">Planned</span>
                          )}
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
                              onClick={() => handleDelete(task.task_id)}
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
        </TabsContent>

        <TabsContent value="bulk" className="space-y-6">
          <MassUploader
            tableName="job_tasks"
            entityName="Job Task"
            sampleData={sampleJobTaskData}
            onUploadComplete={fetchJobTasks}
            requiredFields={['instance_id', 'template_task_id']}
            fieldDescriptions={{
              instance_id: 'Job instance ID (required)',
              template_task_id: 'Template task ID (required)',
              selected_mode_id: 'Task execution mode ID',
              assigned_machine_id: 'Machine resource ID for task execution',
              start_time_minutes: 'Task start time in minutes from schedule start',
              end_time_minutes: 'Task completion time in minutes from schedule start',
              actual_duration_minutes: 'Actual time taken to complete task',
              setup_time_minutes: 'Time required for task setup and preparation'
            }}
          />
        </TabsContent>
      </Tabs>

      {/* Performance Debug Panel (Development Only) */}
      <PerformanceDebugPanel 
        formName="Job Task Form"
        metrics={performanceTracker}
      />
    </div>
  )
}