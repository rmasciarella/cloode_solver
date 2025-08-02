"use client"

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Edit, Trash2 } from 'lucide-react'

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

type Department = {
  department_id: string
  name: string
  code: string
}

interface TemplateTasksTableProps {
  optimizedTasks: OptimizedTask[]
  departments: Department[]
  loading: boolean
  handleEdit: (task: OptimizedTask) => void
  handleDelete: (id: string) => void
}

export function TemplateTasksTable({
  optimizedTasks,
  departments,
  loading,
  handleEdit,
  handleDelete
}: TemplateTasksTableProps) {
  return (
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
  )
}
