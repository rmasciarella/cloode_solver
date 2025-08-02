// Export all services from a central location
export { BaseService } from './base.service'
export { businessCalendarService } from './business-calendar.service'
export { DepartmentService, departmentService } from './department.service'
export { InstanceTaskAssignmentService, instanceTaskAssignmentService } from './instance-task-assignment.service'
export { JobInstanceService, jobInstanceService } from './job-instance.service'
export { JobTemplateService, jobTemplateService } from './job-template.service'
export { MachineService, machineService } from './machine.service'
export { MaintenanceTypeService, maintenanceTypeService } from './maintenance-type.service'
export { OperatorService, operatorService } from './operator.service'
export { OptimizedPrecedenceService, optimizedPrecedenceService } from './optimized-precedence.service'
export { OptimizedTaskService, optimizedTaskService } from './optimized-task.service'
export { OptimizedTaskSetupTimeService, optimizedTaskSetupTimeService } from './optimized-task-setup-time.service'
export { SequenceResourceService, sequenceResourceService } from './sequence-resource.service'
export { SkillService, skillService } from './skill.service'
export { SolverService, solverService } from './solver.service'
export { templateTaskService } from './template-task.service'
export { WorkCellService, workCellService } from './work-cell.service'

// Export types
export type { ServiceResponse, ServiceError } from './base.service'
export type { 
  SolverJobRequest, 
  JobInstanceRequest, 
  ConstraintSettings,
  SolverResponse,
  SolutionResult,
  TaskAssignment,
  ResourceUtilization,
  PerformanceMetrics,
  PatternInfo,
  ValidationResult
} from './solver.service'