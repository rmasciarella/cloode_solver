"use client"

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { supabase } from '@/lib/supabase'
import { useToast } from '@/hooks/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Edit, Trash2 } from 'lucide-react'

type Machine = {
  machine_resource_id: string
  name: string
  capacity: number
  cost_per_hour: number
  department_id: string | null
  cell_id: string
  machine_type: string | null
  is_active: boolean
}

type Department = {
  department_id: string
  name: string
  code: string
}

type WorkCell = {
  cell_id: string
  name: string
  department_id: string | null
}

type MachineFormData = {
  name: string
  capacity: number
  cost_per_hour: number
  department_id: string
  cell_id: string
  machine_type: string
  manufacturer: string
  model: string
  year_installed: number
  is_active: boolean
}

export default function MachineForm() {
  const [machines, setMachines] = useState<Machine[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [workCells, setWorkCells] = useState<WorkCell[]>([])
  const [filteredWorkCells, setFilteredWorkCells] = useState<WorkCell[]>([])
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<MachineFormData>({
    defaultValues: {
      name: '',
      capacity: 1,
      cost_per_hour: 0,
      department_id: '',
      cell_id: '',
      machine_type: '',
      manufacturer: '',
      model: '',
      year_installed: new Date().getFullYear(),
      is_active: true
    }
  })

  const selectedDepartmentId = watch('department_id')

  const fetchMachines = async () => {
    setLoading(true)
    try {
      const { data, error } = await supabase
        .from('machines')
        .select('*')
        .order('name', { ascending: true })

      if (error) throw error
      setMachines(data || [])
    } catch (error) {
      console.error('Error fetching machines:', error)
      toast({
        title: "Error",
        description: "Failed to fetch machines",
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

  const fetchWorkCells = async () => {
    try {
      const { data, error } = await supabase
        .from('work_cells')
        .select('*')
        .order('name', { ascending: true })

      if (error) throw error
      setWorkCells(data || [])
    } catch (error) {
      console.error('Error fetching work cells:', error)
    }
  }

  useEffect(() => {
    fetchMachines()
    fetchDepartments()
    fetchWorkCells()
  }, [])

  // Filter work cells based on selected department
  useEffect(() => {
    if (selectedDepartmentId) {
      setFilteredWorkCells(workCells.filter(cell => cell.department_id === selectedDepartmentId))
    } else {
      setFilteredWorkCells(workCells)
    }
    // Reset cell selection when department changes
    setValue('cell_id', '')
  }, [selectedDepartmentId, workCells, setValue])

  const onSubmit = async (data: MachineFormData) => {
    setIsSubmitting(true)
    try {
      const formData = {
        name: data.name,
        capacity: data.capacity,
        cost_per_hour: data.cost_per_hour,
        department_id: data.department_id || null,
        cell_id: data.cell_id,
        machine_type: data.machine_type || null,
        manufacturer: data.manufacturer || null,
        model: data.model || null,
        year_installed: data.year_installed || null,
        is_active: data.is_active
      }

      if (editingId) {
        const { error } = await supabase
          .from('machines')
          .update(formData)
          .eq('machine_resource_id', editingId)

        if (error) throw error

        toast({
          title: "Success",
          description: "Machine updated successfully"
        })
      } else {
        const { error } = await supabase
          .from('machines')
          .insert([formData])

        if (error) throw error

        toast({
          title: "Success",
          description: "Machine created successfully"
        })
      }

      reset()
      setEditingId(null)
      fetchMachines()
    } catch (error) {
      console.error('Error saving machine:', error)
      toast({
        title: "Error",
        description: "Failed to save machine",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = (machine: Machine) => {
    setEditingId(machine.machine_resource_id)
    setValue('name', machine.name)
    setValue('capacity', machine.capacity)
    setValue('cost_per_hour', machine.cost_per_hour)
    setValue('department_id', machine.department_id || '')
    setValue('cell_id', machine.cell_id)
    setValue('machine_type', machine.machine_type || '')
    setValue('is_active', machine.is_active)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this machine?')) return

    try {
      const { error } = await supabase
        .from('machines')
        .delete()
        .eq('machine_resource_id', id)

      if (error) throw error

      toast({
        title: "Success",
        description: "Machine deleted successfully"
      })
      fetchMachines()
    } catch (error) {
      console.error('Error deleting machine:', error)
      toast({
        title: "Error",
        description: "Failed to delete machine",
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
          <CardTitle>{editingId ? 'Edit Machine' : 'Create New Machine'}</CardTitle>
          <CardDescription>
            {editingId ? 'Update machine information' : 'Add a new machine resource to the production system'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Name - Required */}
              <div className="space-y-2">
                <Label htmlFor="name">Machine Name *</Label>
                <Input
                  id="name"
                  {...register('name', { 
                    required: 'Machine name is required',
                    maxLength: { value: 255, message: 'Name must be 255 characters or less' }
                  })}
                  placeholder="e.g., CNC Machine 01"
                />
                {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
              </div>

              {/* Machine Type */}
              <div className="space-y-2">
                <Label htmlFor="machine_type">Machine Type</Label>
                <Input
                  id="machine_type"
                  {...register('machine_type')}
                  placeholder="e.g., CNC, Assembly, Testing"
                />
              </div>

              {/* Department - Foreign Key Dropdown */}
              <div className="space-y-2">
                <Label htmlFor="department_id">Department</Label>
                <Select onValueChange={(value) => setValue('department_id', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select department" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No Department</SelectItem>
                    {departments.map((dept) => (
                      <SelectItem key={dept.department_id} value={dept.department_id}>
                        {dept.name} ({dept.code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Work Cell - Required, Filtered by Department */}
              <div className="space-y-2">
                <Label htmlFor="cell_id">Work Cell *</Label>
                <Select onValueChange={(value) => setValue('cell_id', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select work cell" />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredWorkCells.map((cell) => (
                      <SelectItem key={cell.cell_id} value={cell.cell_id}>
                        {cell.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {!watch('cell_id') && <p className="text-sm text-red-600">Work cell is required</p>}
              </div>

              {/* Capacity */}
              <div className="space-y-2">
                <Label htmlFor="capacity">Capacity</Label>
                <Input
                  id="capacity"
                  type="number"
                  min="1"
                  {...register('capacity', { 
                    valueAsNumber: true,
                    min: { value: 1, message: 'Capacity must be at least 1' }
                  })}
                />
                {errors.capacity && <p className="text-sm text-red-600">{errors.capacity.message}</p>}
              </div>

              {/* Hourly Cost */}
              <div className="space-y-2">
                <Label htmlFor="cost_per_hour">Hourly Cost ($)</Label>
                <Input
                  id="cost_per_hour"
                  type="number"
                  min="0"
                  step="0.01"
                  {...register('cost_per_hour', { 
                    valueAsNumber: true,
                    min: { value: 0, message: 'Cost must be non-negative' }
                  })}
                />
                {errors.cost_per_hour && <p className="text-sm text-red-600">{errors.cost_per_hour.message}</p>}
              </div>

              {/* Manufacturer */}
              <div className="space-y-2">
                <Label htmlFor="manufacturer">Manufacturer</Label>
                <Input
                  id="manufacturer"
                  {...register('manufacturer')}
                  placeholder="e.g., Haas, Fanuc, Siemens"
                />
              </div>

              {/* Model */}
              <div className="space-y-2">
                <Label htmlFor="model">Model</Label>
                <Input
                  id="model"
                  {...register('model')}
                  placeholder="e.g., VF-2SS, R-2000iB"
                />
              </div>

              {/* Year Installed */}
              <div className="space-y-2">
                <Label htmlFor="year_installed">Year Installed</Label>
                <Input
                  id="year_installed"
                  type="number"
                  min="1980"
                  max={new Date().getFullYear() + 5}
                  {...register('year_installed', { 
                    valueAsNumber: true,
                    min: { value: 1980, message: 'Year must be 1980 or later' },
                    max: { value: new Date().getFullYear() + 5, message: 'Year cannot be more than 5 years in the future' }
                  })}
                />
                {errors.year_installed && <p className="text-sm text-red-600">{errors.year_installed.message}</p>}
              </div>
            </div>

            {/* Active Checkbox */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_active"
                checked={watch('is_active')}
                onCheckedChange={(checked) => setValue('is_active', checked as boolean)}
              />
              <Label htmlFor="is_active">Active</Label>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-2 pt-4">
              {editingId && (
                <Button type="button" variant="outline" onClick={handleCancel}>
                  Cancel
                </Button>
              )}
              <Button type="submit" disabled={isSubmitting || !watch('cell_id')}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {editingId ? 'Update' : 'Create'} Machine
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Machines List */}
      <Card>
        <CardHeader>
          <CardTitle>Machines</CardTitle>
          <CardDescription>Manage existing machines</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : machines.length === 0 ? (
            <p className="text-center text-gray-500 py-4">No machines found</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Name</th>
                    <th className="text-left p-2">Type</th>
                    <th className="text-left p-2">Department</th>
                    <th className="text-left p-2">Capacity</th>
                    <th className="text-left p-2">Cost/Hour</th>
                    <th className="text-left p-2">Status</th>
                    <th className="text-left p-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {machines.map((machine) => {
                    const department = departments.find(d => d.department_id === machine.department_id)
                    const workCell = workCells.find(c => c.cell_id === machine.cell_id)
                    return (
                      <tr key={machine.machine_resource_id} className="border-b hover:bg-gray-50">
                        <td className="p-2 font-medium">{machine.name}</td>
                        <td className="p-2">{machine.machine_type || '-'}</td>
                        <td className="p-2">
                          <div>
                            {department ? `${department.name} (${department.code})` : '-'}
                            {workCell && <div className="text-xs text-gray-500">Cell: {workCell.name}</div>}
                          </div>
                        </td>
                        <td className="p-2">{machine.capacity}</td>
                        <td className="p-2">${machine.cost_per_hour.toFixed(2)}</td>
                        <td className="p-2">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            machine.is_active 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {machine.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="p-2">
                          <div className="flex space-x-1">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleEdit(machine)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDelete(machine.machine_resource_id)}
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