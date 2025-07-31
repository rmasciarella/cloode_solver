"use client"

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { supabase } from '@/lib/supabase'
import { useToast } from '@/hooks/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Edit, Trash2 } from 'lucide-react'

type JobTemplate = {
  pattern_id: string
  name: string
  description: string | null
  task_count: number
  total_min_duration_minutes: number
  critical_path_length_minutes: number
  baseline_performance_seconds: number | null
  optimized_performance_seconds: number | null
  speedup_factor: number | null
  last_benchmarked_at: string | null
  performance_target_seconds: number | null
  solver_parameters: any
  optimization_techniques_applied: string[] | null
  symmetry_breaking_enabled: boolean
  redundant_constraints_count: number
  is_blessed: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

type Department = {
  department_id: string
  name: string
  code: string
}

type JobTemplateFormData = {
  name: string
  description: string
  solver_parameters: string
  task_count: number
  total_min_duration_minutes: number
  critical_path_length_minutes: number
}

const defaultSolverParameters = {
  "num_search_workers": 8,
  "max_time_in_seconds": 60,
  "linearization_level": 1,
  "search_branching": "FIXED_SEARCH",
  "cp_model_presolve": true,
  "repair_hint": true
}

export default function JobTemplateForm() {
  const [jobTemplates, setJobTemplates] = useState<JobTemplate[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<JobTemplateFormData>({
    defaultValues: {
      name: '',
      description: '',
      solver_parameters: JSON.stringify(defaultSolverParameters, null, 2),
      task_count: 1,
      total_min_duration_minutes: 60,
      critical_path_length_minutes: 60
    }
  })

  const fetchJobTemplates = async () => {
    setLoading(true)
    try {
      const { data, error } = await supabase
        .from('job_optimized_patterns')
        .select('*')
        .order('name', { ascending: true })

      if (error) throw error
      setJobTemplates(data || [])
    } catch (error) {
      console.error('Error fetching job templates:', error)
      toast({
        title: "Error",
        description: "Failed to fetch job templates",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchDepartments = async () => {
    try {
      const { data, error } = await supabase
        .from('departments')
        .select('department_id, name, code')
        .eq('is_active', true)
        .order('name', { ascending: true })

      if (error) throw error
      setDepartments(data || [])
    } catch (error) {
      console.error('Error fetching departments:', error)
    }
  }

  useEffect(() => {
    fetchJobTemplates()
    fetchDepartments()
  }, [])

  const onSubmit = async (data: JobTemplateFormData) => {
    setIsSubmitting(true)
    try {
      // Validate JSON
      let parsedSolverParameters
      try {
        parsedSolverParameters = JSON.parse(data.solver_parameters)
      } catch (e) {
        toast({
          title: "Error",
          description: "Solver parameters must be valid JSON",
          variant: "destructive"
        })
        setIsSubmitting(false)
        return
      }

      const formData = {
        name: data.name,
        description: data.description || null,
        solver_parameters: parsedSolverParameters,
        task_count: data.task_count,
        total_min_duration_minutes: data.total_min_duration_minutes,
        critical_path_length_minutes: data.critical_path_length_minutes
      }

      if (editingId) {
        const { error } = await supabase
          .from('job_optimized_patterns')
          .update(formData)
          .eq('pattern_id', editingId)

        if (error) throw error

        toast({
          title: "Success",
          description: "Job template updated successfully"
        })
      } else {
        const { error } = await supabase
          .from('job_optimized_patterns')
          .insert([formData])

        if (error) throw error

        toast({
          title: "Success",
          description: "Job template created successfully"
        })
      }

      reset()
      setEditingId(null)
      fetchJobTemplates()
    } catch (error) {
      console.error('Error saving job template:', error)
      console.error('Error details:', {
        message: error?.message,
        details: error?.details,
        hint: error?.hint,
        code: error?.code
      })
      toast({
        title: "Error",
        description: error?.message || "Failed to save job template",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = (template: JobTemplate) => {
    setEditingId(template.pattern_id)
    setValue('name', template.name)
    setValue('description', template.description || '')
    setValue('solver_parameters', JSON.stringify(template.solver_parameters, null, 2))
    setValue('task_count', template.task_count || 1)
    setValue('total_min_duration_minutes', template.total_min_duration_minutes || 60)
    setValue('critical_path_length_minutes', template.critical_path_length_minutes || 60)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this job template?')) return

    try {
      const { error } = await supabase
        .from('job_optimized_patterns')
        .delete()
        .eq('pattern_id', id)

      if (error) throw error

      toast({
        title: "Success",
        description: "Job template deleted successfully"
      })
      fetchJobTemplates()
    } catch (error) {
      console.error('Error deleting job template:', error)
      toast({
        title: "Error",
        description: "Failed to delete job template",
        variant: "destructive"
      })
    }
  }

  const handleCancel = () => {
    reset()
    setEditingId(null)
  }

  return (
    <div className="space-y-6">
      {/* Form Card */}
      <Card>
        <CardHeader>
          <CardTitle>{editingId ? 'Edit Job Template' : 'Create New Job Template'}</CardTitle>
          <CardDescription>
            {editingId ? 'Update job template information' : 'Add a reusable job template for manufacturing scheduling'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Name - Required */}
              <div className="space-y-2">
                <Label htmlFor="name">Template Name *</Label>
                <Input
                  id="name"
                  {...register('name', { 
                    required: 'Template name is required',
                    maxLength: { value: 255, message: 'Name must be 255 characters or less' }
                  })}
                  placeholder="e.g., Standard Manufacturing Template"
                />
                {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
              </div>


              {/* Task Count */}
              <div className="space-y-2">
                <Label htmlFor="task_count">Task Count *</Label>
                <Input
                  id="task_count"
                  type="number"
                  min="1"
                  {...register('task_count', { 
                    valueAsNumber: true,
                    required: 'Task count is required',
                    min: { value: 1, message: 'Must have at least 1 task' }
                  })}
                  placeholder="1"
                />
                <p className="text-xs text-gray-500">Number of tasks in this pattern</p>
                {errors.task_count && <p className="text-sm text-red-600">{errors.task_count.message}</p>}
              </div>

              {/* Total Min Duration */}
              <div className="space-y-2">
                <Label htmlFor="total_min_duration_minutes">Total Min Duration (minutes)</Label>
                <Input
                  id="total_min_duration_minutes"
                  type="number"
                  min="0"
                  {...register('total_min_duration_minutes', { 
                    valueAsNumber: true,
                    min: { value: 0, message: 'Duration must be non-negative' }
                  })}
                  placeholder="60"
                />
                <p className="text-xs text-gray-500">Sum of minimum task durations</p>
                {errors.total_min_duration_minutes && <p className="text-sm text-red-600">{errors.total_min_duration_minutes.message}</p>}
              </div>

              {/* Critical Path Length */}
              <div className="space-y-2">
                <Label htmlFor="critical_path_length_minutes">Critical Path Length (minutes)</Label>
                <Input
                  id="critical_path_length_minutes"
                  type="number"
                  min="0"
                  {...register('critical_path_length_minutes', { 
                    valueAsNumber: true,
                    min: { value: 0, message: 'Length must be non-negative' }
                  })}
                  placeholder="60"
                />
                <p className="text-xs text-gray-500">Minimum time to complete pattern (longest path)</p>
                {errors.critical_path_length_minutes && <p className="text-sm text-red-600">{errors.critical_path_length_minutes.message}</p>}
              </div>

            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                {...register('description')}
                placeholder="Template description and use cases"
                rows={3}
              />
            </div>

            {/* Blessed Solver Parameters */}
            <div className="space-y-2">
              <Label htmlFor="solver_parameters">Blessed Solver Parameters (JSON) *</Label>
              <Textarea
                id="solver_parameters"
                {...register('solver_parameters', { 
                  required: 'Solver parameters are required',
                  validate: (value) => {
                    try {
                      JSON.parse(value)
                      return true
                    } catch (e) {
                      return 'Must be valid JSON'
                    }
                  }
                })}
                rows={8}
                className="font-mono text-sm"
                placeholder={JSON.stringify(defaultSolverParameters, null, 2)}
              />
              {errors.solver_parameters && <p className="text-sm text-red-600">{errors.solver_parameters.message}</p>}
              <p className="text-xs text-gray-500">
                Configure CP-SAT solver parameters for optimal performance. Default values shown above are production-tested.
              </p>
            </div>


            {/* Action Buttons */}
            <div className="flex justify-end space-x-2 pt-4">
              {editingId && (
                <Button type="button" variant="outline" onClick={handleCancel}>
                  Cancel
                </Button>
              )}
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {editingId ? 'Update' : 'Create'} Template
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Templates List */}
      <Card>
        <CardHeader>
          <CardTitle>Job Templates</CardTitle>
          <CardDescription>Manage existing job templates</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : jobTemplates.length === 0 ? (
            <p className="text-center text-gray-500 py-4">No job templates found</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Name</th>
                    <th className="text-left p-2">Task Count</th>
                    <th className="text-left p-2">Description</th>
                    <th className="text-left p-2">Created</th>
                    <th className="text-left p-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobTemplates.map((template) => {
                    return (
                      <tr key={template.pattern_id} className="border-b hover:bg-gray-50">
                        <td className="p-2 font-medium">{template.name}</td>
                        <td className="p-2">{template.task_count}</td>
                        <td className="p-2">{template.description || '-'}</td>
                        <td className="p-2">
                          {new Date(template.created_at).toLocaleDateString()}
                        </td>
                        <td className="p-2">
                          <div className="flex space-x-1">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleEdit(template)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDelete(template.pattern_id)}
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