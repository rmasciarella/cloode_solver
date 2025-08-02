"use client"

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Edit, Trash2 } from 'lucide-react'

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

interface JobTasksTableProps {
  jobTasks: JobTask[]
  jobInstances: JobInstance[]
  templateTasks: TemplateTask[]
  taskModes: TemplateTaskMode[]
  machines: Machine[]
  loading: boolean
  handleEdit: (task: JobTask) => void
  handleDelete: (id: string) => void
}

export function JobTasksTable({
  jobTasks,
  jobInstances,
  templateTasks,
  taskModes,
  machines,
  loading,
  handleEdit,
  handleDelete
}: JobTasksTableProps) {
  return (
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
  )
}
