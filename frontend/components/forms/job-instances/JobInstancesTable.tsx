"use client"

import { Button } from '@/components/ui/button'
import { Loader2, Edit, Trash2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface JobInstancesTableProps {
  jobInstances: any[]
  departments: any[]
  onEdit: (instance: any) => void
  onDelete: (id: string) => void
  loading: boolean
}

export function JobInstancesTable({
  jobInstances,
  departments,
  onEdit,
  onDelete,
  loading
}: JobInstancesTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Job Instances</CardTitle>
        <CardDescription>Manage existing job instances</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center py-4">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : jobInstances.length === 0 ? (
          <p className="text-center text-gray-500 py-4">No job instances found</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Name</th>
                  <th className="text-left p-2">Pattern</th>
                  <th className="text-left p-2">Department</th>
                  <th className="text-left p-2">Priority</th>
                  <th className="text-left p-2">Due Date</th>
                  <th className="text-left p-2">Quantity</th>
                  <th className="text-left p-2">Status</th>
                  <th className="text-left p-2">Est. Cost</th>
                  <th className="text-left p-2">Revenue</th>
                  <th className="text-left p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobInstances.map((instance: any) => {
                  const department = departments.find(d => d.department_id === instance.department_id)
                  return (
                    <tr key={instance.instance_id} className="border-b hover:bg-gray-50">
                      <td className="p-2 font-medium">
                        <div>
                          {instance.name}
                          {instance.customer_order_id && (
                            <div className="text-xs text-gray-500">Order: {instance.customer_order_id}</div>
                          )}
                        </div>
                      </td>
                      <td className="p-2">{instance.job_templates?.name || 'Unknown'}</td>
                      <td className="p-2">{department ? `${department.name} (${department.code})` : '-'}</td>
                      <td className="p-2">{instance.priority}</td>
                      <td className="p-2">
                        {instance.due_date ? new Date(instance.due_date).toLocaleDateString() : '-'}
                      </td>
                      <td className="p-2">{instance.quantity}</td>
                      <td className="p-2">
                        <span className={`px-2 py-1 rounded-full text-xs capitalize ${
                          instance.status === 'completed' 
                            ? 'bg-green-100 text-green-800'
                            : instance.status === 'in_progress'
                            ? 'bg-blue-100 text-blue-800'
                            : instance.status === 'cancelled'
                            ? 'bg-red-100 text-red-800'
                            : instance.status === 'on_hold'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {instance.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="p-2">
                        {instance.estimated_cost ? `$${instance.estimated_cost.toFixed(2)}` : '-'}
                      </td>
                      <td className="p-2">
                        {instance.revenue_value ? `$${instance.revenue_value.toFixed(2)}` : '-'}
                      </td>
                      <td className="p-2">
                        <div className="flex space-x-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onEdit(instance)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onDelete(instance.instance_id)}
                            className="text-red-600 hover:bg-red-50"
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
