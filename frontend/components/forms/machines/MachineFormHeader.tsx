"use client"

import { Button } from '@/components/ui/button'
import { Card, _CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { RefreshCw, Plus } from 'lucide-react'

interface MachineFormHeaderProps {
  loading: boolean
  onRefresh: () => Promise<void>
  onAddNew: () => void
  className?: string
}

export function MachineFormHeader({
  loading,
  onRefresh,
  onAddNew,
  className = ""
}: MachineFormHeaderProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Machine Management</CardTitle>
            <CardDescription>
              Manage machine resources, capacities, and configurations
            </CardDescription>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            
            <Button
              size="sm"
              onClick={onAddNew}
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Machine
            </Button>
          </div>
        </div>
      </CardHeader>
    </Card>
  )
}