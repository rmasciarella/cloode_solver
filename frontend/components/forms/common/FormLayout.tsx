"use client"

import { ReactNode } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Loader2 } from 'lucide-react'

interface FormTab {
  value: string
  label: string
  content: ReactNode
  ariaLabel?: string
}

interface FormLayoutProps {
  title: string
  description: string
  tabs: FormTab[]
  activeTab: string
  onTabChange: (value: string) => void
  loading?: boolean
}

export function FormLayout({
  title,
  description,
  tabs,
  activeTab,
  onTabChange,
  loading = false
}: FormLayoutProps) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={onTabChange}>
          <TabsList 
            className={`grid w-full grid-cols-${tabs.length}`} 
            role="tablist"
            aria-label={`${title} navigation tabs`}
          >
            {tabs.map(tab => (
              <TabsTrigger 
                key={tab.value} 
                value={tab.value} 
                role="tab" 
                aria-selected={activeTab === tab.value}
                aria-label={tab.ariaLabel || tab.label}
              >
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>

          {loading ? (
            <div className="flex justify-center p-8" role="status" aria-live="polite">
              <Loader2 className="h-8 w-8 animate-spin" aria-label="Loading" />
              <span className="sr-only">Loading...</span>
            </div>
          ) : (
            tabs.map(tab => (
              <TabsContent 
                key={tab.value} 
                value={tab.value} 
                className="space-y-4" 
                role="tabpanel"
                aria-labelledby={`tab-${tab.value}`}
              >
                {tab.content}
              </TabsContent>
            ))
          )}
        </Tabs>
      </CardContent>
    </Card>
  )
}