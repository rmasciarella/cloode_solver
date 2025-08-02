"use client"

import { Button } from '@/components/ui/button'
import { Loader2, Edit, Trash2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface OperatorsTableProps {
  operators: any[]
  departments: any[]
  onEdit: (operator: any) => void
  onDelete: (id: string) => void
  loading: boolean
}

export function OperatorsTable({
  operators,
  departments,
  onEdit,
  onDelete,
  loading
}: OperatorsTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Operators</CardTitle>
        <CardDescription>Manage existing operators</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center py-4">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : operators.length === 0 ? (
          <p className="text-center text-gray-500 py-4">No operators found</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Name</th>
                  <th className="text-left p-2">Employee #</th>
                  <th className="text-left p-2">Department</th>
                  <th className="text-left p-2">Rate/Hour</th>
                  <th className="text-left p-2">Max Hours</th>
                  <th className="text-left p-2">Ratings</th>
                  <th className="text-left p-2">Status</th>
                  <th className="text-left p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {operators.map((operator) => {
                  const department = departments.find(d => d.department_id === operator.department_id)
                  return (
                    <tr key={operator.operator_id} className="border-b hover:bg-gray-50">
                      <td className="p-2 font-medium">{operator.name}</td>
                      <td className="p-2">{operator.employee_number || '-'}</td>
                      <td className="p-2">{department ? `${department.name} (${department.code})` : '-'}</td>
                      <td className="p-2">${operator.hourly_rate.toFixed(2)}</td>
                      <td className="p-2">
                        <div className="text-sm">
                          <div>{operator.max_hours_per_day}h/day</div>
                          <div className="text-gray-500">{operator.max_hours_per_week}h/week</div>
                        </div>
                      </td>
                      <td className="p-2">
                        <div className="text-sm">
                          <div>Eff: {operator.efficiency_rating.toFixed(2)}</div>
                          <div>Qual: {operator.quality_score.toFixed(2)}</div>
                          <div>Safe: {operator.safety_score.toFixed(2)}</div>
                        </div>
                      </td>
                      <td className="p-2">
                        <div className="flex flex-col space-y-1">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            operator.employment_status === 'active' 
                              ? 'bg-green-100 text-green-800' 
                              : operator.employment_status === 'on_leave'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {operator.employment_status.replace('_', ' ')}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            operator.is_active 
                              ? 'bg-blue-100 text-blue-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {operator.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                      </td>
                      <td className="p-2">
                        <div className="flex space-x-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onEdit(operator)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onDelete(operator.operator_id)}
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
