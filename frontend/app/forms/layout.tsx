"use client"

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Building2, Factory, Users, Calendar, BookTemplate as FileTemplate, Network, Cog, Settings, Clock, Wrench, BriefcaseIcon, ListTodo, Menu, X } from 'lucide-react'
import { ArchitecturalPerformanceMonitor } from '@/components/monitoring/ArchitecturalPerformanceMonitor'

const navigationSections = [
  {
    title: 'Organization',
    icon: Building2,
    items: [
      { key: 'departments', label: 'Departments', icon: Building2, href: '/forms/departments' },
      { key: 'work-cells', label: 'Work Cells', icon: Factory, href: '/forms/work-cells' },
      { key: 'business-calendars', label: 'Business Calendars', icon: Calendar, href: '/forms/business-calendars' },
    ]
  },
  {
    title: 'Templates',
    icon: FileTemplate,
    items: [
      { key: 'job-templates', label: 'Job Templates', icon: FileTemplate, href: '/forms/job-templates' },
      { key: 'template-tasks', label: 'Template Tasks', icon: ListTodo, href: '/forms/template-tasks' },
      { key: 'template-precedence', label: 'Template Precedences', icon: Network, href: '/forms/template-precedence' },
    ]
  },
  {
    title: 'Resources',
    icon: Cog,
    items: [
      { key: 'machines', label: 'Machines', icon: Cog, href: '/forms/machines' },
      { key: 'operators', label: 'Operators', icon: Users, href: '/forms/operators' },
      { key: 'skills', label: 'Skills', icon: Settings, href: '/forms/skills' },
      { key: 'sequence-resources', label: 'Sequence Resources', icon: Network, href: '/forms/sequence-resources' },
    ]
  },
  {
    title: 'Scheduling',
    icon: Clock,
    items: [
      { key: 'setup-times', label: 'Setup Times', icon: Clock, href: '/forms/setup-times' },
      { key: 'maintenance-types', label: 'Maintenance Types', icon: Wrench, href: '/forms/maintenance-types' },
    ]
  },
  {
    title: 'Jobs',
    icon: BriefcaseIcon,
    items: [
      { key: 'job-instances', label: 'Job Instances', icon: BriefcaseIcon, href: '/forms/job-instances' },
      { key: 'job-tasks', label: 'Job Tasks', icon: ListTodo, href: '/forms/job-tasks' },
    ]
  },
]

interface FormsLayoutProps {
  children: React.ReactNode
}

export default function FormsLayout({ children }: FormsLayoutProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    'Organization': true,
    'Templates': false,
    'Resources': false,
    'Scheduling': false,
    'Jobs': false,
  })
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pathname = usePathname()

  const toggleSection = (title: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [title]: !prev[title]
    }))
  }

  const getSectionTitle = () => {
    for (const section of navigationSections) {
      const item = section.items.find(item => pathname === item.href)
      if (item) {
        return item.label
      }
    }
    return 'Vulcan MES'
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 bg-white rounded-md shadow-md hover:bg-gray-50 transition-colors"
        >
          {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed lg:static inset-y-0 left-0 z-50 w-80 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out",
        sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-6 border-b border-gray-200">
            <Link href="/" className="block">
              <h1 className="text-xl font-bold text-gray-900">Vulcan MES</h1>
              <p className="text-sm text-gray-600 mt-1">Manufacturing Execution System</p>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto py-4">
            {navigationSections.map((section) => (
              <div key={section.title} className="mb-2">
                <button
                  onClick={() => toggleSection(section.title)}
                  className="flex items-center justify-between w-full px-6 py-3 text-left text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center">
                    <section.icon className="mr-3 h-5 w-5 text-gray-500" />
                    {section.title}
                  </div>
                  <div className={cn(
                    "transform transition-transform duration-200",
                    expandedSections[section.title] ? "rotate-90" : "rotate-0"
                  )}>
                    ▶
                  </div>
                </button>
                
                {expandedSections[section.title] && (
                  <div className="ml-4 border-l border-gray-200">
                    {section.items.map((item) => (
                      <Link
                        key={item.key}
                        href={item.href}
                        onClick={() => setSidebarOpen(false)}
                        className={cn(
                          "flex items-center w-full pl-8 pr-6 py-2 text-sm transition-colors",
                          pathname === item.href
                            ? "text-blue-700 bg-blue-50 border-r-2 border-blue-700"
                            : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                        )}
                      >
                        <item.icon className="mr-3 h-4 w-4" />
                        {item.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>

          {/* Footer */}
          <div className="p-6 border-t border-gray-200">
            <div className="text-xs text-gray-500">
              <p>Version 1.0.0</p>
              <p>Manufacturing Scheduling</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center">
            <h2 className="text-2xl font-semibold text-gray-900 ml-12 lg:ml-0">
              {getSectionTitle()}
            </h2>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl">
            {children}
          </div>
        </main>
      </div>

      {/* Performance Monitoring */}
      <ArchitecturalPerformanceMonitor 
        routeName={pathname}
        formComponent={getSectionTitle()}
      />
    </div>
  )
}