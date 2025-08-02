import Link from 'next/link'
import type { Metadata } from 'next'
import { Building2, Factory, Users, Calendar, BookTemplate as FileTemplate, Network, Cog, Settings, Clock, Wrench, BriefcaseIcon, ListTodo } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Dashboard - Vulcan MES',
  description: 'Manufacturing execution system dashboard with quick access to all configuration forms and modules',
}

const dashboardSections = [
  {
    title: 'Organization',
    description: 'Manage departments, work cells, and business calendars',
    icon: Building2,
    items: [
      { key: 'departments', label: 'Departments', icon: Building2, href: '/forms/departments', description: 'Manage organizational departments' },
      { key: 'work-cells', label: 'Work Cells', icon: Factory, href: '/forms/work-cells', description: 'Configure manufacturing work cells' },
      { key: 'business-calendars', label: 'Business Calendars', icon: Calendar, href: '/forms/business-calendars', description: 'Set up business calendars and schedules' },
    ]
  },
  {
    title: 'Templates',
    description: 'Configure job templates and task structures',
    icon: FileTemplate,
    items: [
      { key: 'job-templates', label: 'Job Templates', icon: FileTemplate, href: '/forms/job-templates', description: 'Create and manage job templates' },
      { key: 'template-tasks', label: 'Template Tasks', icon: ListTodo, href: '/forms/template-tasks', description: 'Define tasks within job templates' },
      { key: 'template-precedence', label: 'Template Precedences', icon: Network, href: '/forms/template-precedence', description: 'Set task dependencies and precedences' },
    ]
  },
  {
    title: 'Resources',
    description: 'Manage machines, operators, and capabilities',
    icon: Cog,
    items: [
      { key: 'machines', label: 'Machines', icon: Cog, href: '/forms/machines', description: 'Configure manufacturing machines' },
      { key: 'operators', label: 'Operators', icon: Users, href: '/forms/operators', description: 'Manage operator profiles and assignments' },
      { key: 'skills', label: 'Skills', icon: Settings, href: '/forms/skills', description: 'Define operator skills and capabilities' },
      { key: 'sequence-resources', label: 'Sequence Resources', icon: Network, href: '/forms/sequence-resources', description: 'Configure sequence-specific resources' },
    ]
  },
  {
    title: 'Scheduling',
    description: 'Set up scheduling parameters and constraints',
    icon: Clock,
    items: [
      { key: 'setup-times', label: 'Setup Times', icon: Clock, href: '/forms/setup-times', description: 'Configure machine setup and changeover times' },
      { key: 'maintenance-types', label: 'Maintenance Types', icon: Wrench, href: '/forms/maintenance-types', description: 'Define maintenance schedules and types' },
    ]
  },
  {
    title: 'Jobs',
    description: 'Manage active jobs and production tasks',
    icon: BriefcaseIcon,
    items: [
      { key: 'job-instances', label: 'Job Instances', icon: BriefcaseIcon, href: '/forms/job-instances', description: 'Create and track job instances' },
      { key: 'job-tasks', label: 'Job Tasks', icon: ListTodo, href: '/forms/job-tasks', description: 'Manage individual job tasks' },
    ]
  },
]

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Vulcan MES Dashboard</h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Manufacturing Execution System - Configure your production environment, manage resources, and optimize scheduling workflows.
          </p>
        </div>

        {/* Dashboard Sections */}
        <div className="space-y-12">
          {dashboardSections.map((section) => (
            <div key={section.title} className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
              <div className="flex items-center mb-6">
                <section.icon className="h-8 w-8 text-blue-600 mr-4" />
                <div>
                  <h2 className="text-2xl font-semibold text-gray-900">{section.title}</h2>
                  <p className="text-gray-600 mt-1">{section.description}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {section.items.map((item) => (
                  <Link
                    key={item.key}
                    href={item.href}
                    className="block p-6 bg-gray-50 rounded-lg hover:bg-blue-50 hover:border-blue-200 border border-transparent transition-all duration-200 group"
                  >
                    <div className="flex items-center mb-3">
                      <item.icon className="h-6 w-6 text-gray-500 group-hover:text-blue-600 mr-3" />
                      <h3 className="text-lg font-medium text-gray-900 group-hover:text-blue-900">
                        {item.label}
                      </h3>
                    </div>
                    <p className="text-sm text-gray-600 group-hover:text-gray-700">
                      {item.description}
                    </p>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mt-12 bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Link
              href="/forms/departments"
              className="p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors text-center"
            >
              <Building2 className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <span className="text-sm font-medium text-blue-900">Add Department</span>
            </Link>
            <Link
              href="/forms/machines"
              className="p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors text-center"
            >
              <Cog className="h-8 w-8 text-green-600 mx-auto mb-2" />
              <span className="text-sm font-medium text-green-900">Add Machine</span>
            </Link>
            <Link
              href="/forms/job-templates"
              className="p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors text-center"
            >
              <FileTemplate className="h-8 w-8 text-purple-600 mx-auto mb-2" />
              <span className="text-sm font-medium text-purple-900">Create Template</span>
            </Link>
            <Link
              href="/forms/job-instances"
              className="p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors text-center"
            >
              <BriefcaseIcon className="h-8 w-8 text-orange-600 mx-auto mb-2" />
              <span className="text-sm font-medium text-orange-900">Start Job</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}