"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { skillService, departmentService } from '@/lib/services'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MassUploader } from '@/components/ui/mass-uploader'
import { Loader2 } from 'lucide-react'
import { 
  useFormPerformance, 
  useFormData, 
  useFormSubmission, 
  useMultipleFormData 
} from '@/hooks/forms'
import { SkillFormFields } from './SkillFormFields'
import { SkillsTable } from './SkillsTable'

interface SkillFormData {
  name: string
  description: string
  category: string
  department_id: string
  complexity_level: string
  training_hours_required: number
  certification_required: boolean
  certification_expires_after_months: number
  market_hourly_rate: number
  skill_scarcity_level: string
  is_active: boolean
}

interface Skill {
  skill_id: string
  name: string
  description: string | null
  category: string | null
  department_id: string | null
  complexity_level: string
  training_hours_required: number
  certification_required: boolean
  certification_expires_after_months: number | null
  market_hourly_rate: number | null
  skill_scarcity_level: string
  is_active: boolean
  created_at: string
}

const sampleSkillData = [
  {
    name: "Welding",
    description: "Metal joining and fabrication skills",
    category: "mechanical",
    department_id: "dept_123",
    complexity_level: "intermediate",
    training_hours_required: 80,
    certification_required: true,
    certification_expires_after_months: 24,
    market_hourly_rate: 35.50,
    skill_scarcity_level: "uncommon",
    is_active: true
  }
]

export default function SkillFormRefactored() {
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null)
  const [activeTab, setActiveTab] = useState('list')

  // Use performance tracking hook
  const { 
    trackInteraction, 
    trackFieldFocus, 
    trackError 
  } = useFormPerformance('SkillForm')

  // Use data fetching hooks
  const { 
    data: skills, 
    loading: skillsLoading, 
    refresh: refreshSkills 
  } = useFormData({
    fetchFn: skillService.getAll
  })

  const { 
    data: departments, 
    loading: departmentsLoading 
  } = useFormData({
    fetchFn: departmentService.getAll
  })

  // Form setup
  const form = useForm<SkillFormData>({
    defaultValues: {
      name: '',
      description: '',
      category: '',
      department_id: '',
      complexity_level: 'basic',
      training_hours_required: 0,
      certification_required: false,
      certification_expires_after_months: 0,
      market_hourly_rate: 0,
      skill_scarcity_level: 'common',
      is_active: true
    }
  })

  // Use form submission hook
  const { handleSubmit: submitForm, submitting } = useFormSubmission({
    onSubmit: async (data: SkillFormData) => {
      if (editingSkill) {
        await skillService.update(editingSkill.skill_id, data)
      } else {
        await skillService.create(data)
      }
    },
    onSuccess: () => {
      form.reset()
      setEditingSkill(null)
      setActiveTab('list')
      refreshSkills()
    },
    onError: trackError,
    successMessage: editingSkill ? "Skill updated successfully" : "Skill created successfully",
    formName: 'SkillForm'
  })

  const handleEdit = (skill: Skill) => {
    setEditingSkill(skill)
    form.reset({
      name: skill.name,
      description: skill.description || '',
      category: skill.category || '',
      department_id: skill.department_id || '',
      complexity_level: skill.complexity_level,
      training_hours_required: skill.training_hours_required,
      certification_required: skill.certification_required,
      certification_expires_after_months: skill.certification_expires_after_months || 0,
      market_hourly_rate: skill.market_hourly_rate || 0,
      skill_scarcity_level: skill.skill_scarcity_level,
      is_active: skill.is_active
    })
    setActiveTab('create')
    trackInteraction()
  }

  const handleDelete = async (skillId: string) => {
    if (confirm('Are you sure you want to delete this skill?')) {
      try {
        await skillService.delete(skillId)
        refreshSkills()
      } catch (error) {
        trackError()
      }
    }
    trackInteraction()
  }

  const handleCancel = () => {
    form.reset()
    setEditingSkill(null)
    setActiveTab('list')
    trackInteraction()
  }

  const loading = skillsLoading || departmentsLoading

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Skill Management</CardTitle>
        <CardDescription>
          Define and manage technical skills required across your organization
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3" role="tablist">
            <TabsTrigger value="list" role="tab" aria-selected={activeTab === 'list'}>
              View Skills
            </TabsTrigger>
            <TabsTrigger value="create" role="tab" aria-selected={activeTab === 'create'}>
              {editingSkill ? 'Edit Skill' : 'Create Skill'}
            </TabsTrigger>
            <TabsTrigger value="bulk" role="tab" aria-selected={activeTab === 'bulk'}>
              Bulk Upload
            </TabsTrigger>
          </TabsList>

          <TabsContent value="list" className="space-y-4" role="tabpanel">
            {loading ? (
              <div className="flex justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : (
              <SkillsTable
                skills={skills}
                departments={departments}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            )}
          </TabsContent>

          <TabsContent value="create" className="space-y-4" role="tabpanel">
            <form onSubmit={form.handleSubmit(submitForm)} noValidate>
              <SkillFormFields
                form={form}
                departments={departments}
                onFieldFocus={trackFieldFocus}
                onInteraction={trackInteraction}
              />

              <div className="flex gap-3 mt-6">
                <Button
                  type="submit"
                  disabled={submitting}
                  aria-busy={submitting}
                >
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {editingSkill ? 'Update' : 'Create'} Skill
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleCancel}
                  disabled={submitting}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </TabsContent>

          <TabsContent value="bulk" className="space-y-6" role="tabpanel">
            <MassUploader
              tableName="skills"
              entityName="Skill"
              sampleData={sampleSkillData}
              onUploadComplete={refreshSkills}
              requiredFields={['name', 'category', 'department_id', 'complexity_level', 'skill_scarcity_level']}
              fieldDescriptions={{
                name: 'Unique skill name',
                description: 'Detailed description of the skill',
                category: 'One of: mechanical, electrical, quality, assembly, testing, machining, splicing, alignment, cleaning',
                department_id: 'ID of the department this skill belongs to',
                complexity_level: 'One of: basic, intermediate, advanced, expert',
                training_hours_required: 'Number of training hours required',
                certification_required: 'true or false',
                certification_expires_after_months: 'Number of months before certification expires',
                market_hourly_rate: 'Market rate per hour in dollars',
                skill_scarcity_level: 'One of: common, uncommon, rare, critical',
                is_active: 'true or false (default: true)'
              }}
            />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}