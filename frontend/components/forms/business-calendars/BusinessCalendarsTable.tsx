"use client"

import { Button } from '@/components/ui/button'
import { Loader2, Edit, Trash2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getTimeRangeDescription } from '@/lib/timeUtils'

const daysOfWeek = [
  { bit: 0, label: 'Monday', abbr: 'Mon' },
  { bit: 1, label: 'Tuesday', abbr: 'Tue' },
  { bit: 2, label: 'Wednesday', abbr: 'Wed' },
  { bit: 3, label: 'Thursday', abbr: 'Thu' },
  { bit: 4, label: 'Friday', abbr: 'Fri' },
  { bit: 5, label: 'Saturday', abbr: 'Sat' },
  { bit: 6, label: 'Sunday', abbr: 'Sun' }
]

interface BusinessCalendarsTableProps {
  businessCalendars: any[]
  onEdit: (calendar: any) => void
  onDelete: (id: string) => void
  loading: boolean
  onInteraction?: (type: string, field: string) => void
}

export function BusinessCalendarsTable({
  businessCalendars,
  onEdit,
  onDelete,
  loading,
  onInteraction
}: BusinessCalendarsTableProps) {
  const trackInteraction = (type: string, field: string) => {
    onInteraction?.(type, field)
  }

  const workingDaysMaskToArray = (mask: number): boolean[] => {
    return daysOfWeek.map(day => Boolean(mask & (1 << day.bit)))
  }

  const getWorkingDaysDisplay = (mask: number) => {
    const workingDays = workingDaysMaskToArray(mask)
    return daysOfWeek
      .filter((_day, index) => workingDays[index])
      .map(day => day.abbr)
      .join(', ')
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Business Calendars</CardTitle>
        <CardDescription>Manage existing business calendars</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center py-4">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : businessCalendars.length === 0 ? (
          <p className="text-center text-gray-500 py-4">No business calendars found</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Name</th>
                  <th className="text-left p-2">Timezone</th>
                  <th className="text-left p-2">Working Hours</th>
                  <th className="text-left p-2">Working Days</th>
                  <th className="text-left p-2">Status</th>
                  <th className="text-left p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {businessCalendars.map((calendar) => (
                  <tr key={calendar.calendar_id} className="border-b hover:bg-gray-50">
                    <td className="p-2 font-medium">
                      <div>
                        {calendar.name}
                        {calendar.is_default && (
                          <span className="ml-2 px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">Default</span>
                        )}
                      </div>
                    </td>
                    <td className="p-2">{calendar.timezone}</td>
                    <td className="p-2">
                      {getTimeRangeDescription(calendar.default_start_time, calendar.default_end_time)}
                    </td>
                    <td className="p-2 text-sm">{getWorkingDaysDisplay(calendar.working_days_mask)}</td>
                    <td className="p-2">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        calendar.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {calendar.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="p-2">
                      <div className="flex space-x-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            onEdit(calendar)
                            trackInteraction('click', `button#edit-${calendar.calendar_id}`)
                          }}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            onDelete(calendar.calendar_id)
                            trackInteraction('click', `button#delete-${calendar.calendar_id}`)
                          }}
                          className="text-red-600 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
