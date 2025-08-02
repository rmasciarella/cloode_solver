# Phase 3: Maintainability Refactor Guide

**Target Audience**: Developers with refactoring and optimization specialization  
**Prerequisites**: None - Can proceed immediately and run in parallel with other phases  
**Timeline**: 4-6 weeks  
**Scope**: Component decomposition, TypeScript optimization, performance monitoring cleanup

## Overview

This phase focuses on breaking down monolithic components (600-1200 lines) into maintainable, testable units while optimizing TypeScript configuration and streamlining performance monitoring.

## Current State Analysis

### Large Components Requiring Decomposition
```
Priority order (by line count):
1. SkillForm.tsx (1211 lines) ✅ ALREADY REFACTORED
2. MachineForm.tsx (925 lines)
3. SetupTimeForm.tsx (889 lines)  
4. MaintenanceTypeForm.tsx (870 lines)
5. DepartmentForm.tsx (670 lines)
6. JobTemplateForm.tsx (650+ lines)
7. Remaining forms (600+ lines each)
```

### Performance Monitoring Issues
- 5 different tracking systems causing overhead
- 100+ lines per performance hook
- Runtime overhead on every user interaction

### TypeScript Configuration
```json
// Current problematic settings in tsconfig.json
{
  "strict": false,
  "noUnusedLocals": false, 
  "noUnusedParameters": false,
  "exactOptionalPropertyTypes": false
}
```

## Task 1: Component Decomposition (3-4 weeks)

### 1.1 Create Shared Component Library

First, establish reusable components:

```bash
mkdir -p components/shared/forms
mkdir -p components/shared/tables
mkdir -p components/shared/ui
mkdir -p hooks/shared
```

#### Create Base Form Components
```typescript
// components/shared/forms/FormSection.tsx
interface FormSectionProps {
  title: string
  description?: string
  children: React.ReactNode
  collapsible?: boolean
}

// components/shared/forms/FormField.tsx  
interface FormFieldProps<T> {
  name: string
  label: string
  description?: string
  control: Control<T>
  rules?: RegisterOptions
  children: React.ReactNode
}

// components/shared/forms/BulkActionsToolbar.tsx
interface BulkActionsToolbarProps<T> {
  selectedCount: number
  onBulkEdit: (items: T[]) => void
  onBulkDelete: (items: T[]) => void
  onClearSelection: () => void
}
```

#### Create Advanced Table Components
```typescript
// components/shared/tables/DataTable.tsx
interface DataTableProps<T> {
  data: T[]
  columns: ColumnDef<T>[]
  searchPlaceholder?: string
  onRowSelect?: (rows: T[]) => void
  bulkActions?: React.ReactNode
}

// components/shared/tables/TableFilters.tsx
interface TableFiltersProps {
  searchValue: string
  onSearchChange: (value: string) => void
  additionalFilters?: React.ReactNode
}
```

### 1.2 Refactor Forms in Priority Order

#### Example: MachineForm.tsx Decomposition

**Target Structure** (from 925 lines → ~200 lines main + sub-components):

```typescript
// components/forms/MachineForm/index.tsx (Main orchestrator)
export default function MachineForm() {
  // Only orchestration logic (~150-200 lines)
  return (
    <div className="space-y-6">
      <MachineFormHeader />
      <MachineFormFilters />
      <MachineDataTable />
      <MachineFormDialog />
    </div>
  )
}

// components/forms/MachineForm/MachineFormHeader.tsx (~50 lines)
// components/forms/MachineForm/MachineFormFilters.tsx (~100 lines)  
// components/forms/MachineForm/MachineDataTable.tsx (~150 lines)
// components/forms/MachineForm/MachineFormDialog.tsx (~200 lines)
// components/forms/MachineForm/hooks/useMachineForm.ts (~100 lines)
// components/forms/MachineForm/schemas/machineSchema.ts (~50 lines)
```

#### Decomposition Pattern for Each Form

1. **Extract Data Fetching**
   ```typescript
   // hooks/forms/useMachineData.ts
   export function useMachineData() {
     // All data fetching logic
     // Error handling
     // Loading states
   }
   ```

2. **Extract Form Logic**
   ```typescript
   // hooks/forms/useMachineForm.ts  
   export function useMachineForm() {
     // Form state management
     // Validation handling
     // Submit logic
   }
   ```

3. **Extract Schema Definitions**
   ```typescript
   // schemas/machineSchema.ts
   export const machineSchema = z.object({
     // Validation rules
   })
   
   export type MachineFormData = z.infer<typeof machineSchema>
   ```

4. **Create Sub-Components**
   ```typescript
   // Split by functional areas:
   MachineBasicInfo.tsx      (~80 lines)
   MachineCapabilities.tsx   (~100 lines)  
   MachineSchedule.tsx       (~120 lines)
   MachineDataTable.tsx      (~150 lines)
   ```

### 1.3 Refactoring Checklist Per Form

For each form component:

- [ ] **Extract custom hooks** (data fetching, form logic)
- [ ] **Separate schema definitions** into dedicated files
- [ ] **Create sub-components** by functional area
- [ ] **Implement shared components** where applicable
- [ ] **Add component-level tests** for each sub-component
- [ ] **Verify accessibility** (ARIA labels, keyboard navigation)
- [ ] **Performance check** (React DevTools Profiler)

## Task 2: TypeScript Optimization (1 week)

### 2.1 Enable Strict Mode

Update `tsconfig.json`:
```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true, 
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true
  }
}
```

### 2.2 Fix Type Issues

Expected issues and solutions:

1. **Implicit any types**
   ```typescript
   // Before
   function handleSubmit(data) { }
   
   // After  
   function handleSubmit(data: FormData) { }
   ```

2. **Unused parameters**
   ```typescript
   // Before
   function onClick(event, data) { }
   
   // After
   function onClick(_event: Event, data: FormData) { }
   ```

3. **Missing return types**
   ```typescript
   // Before
   function getData() {
     return fetch('/api/data')
   }
   
   // After
   function getData(): Promise<Response> {
     return fetch('/api/data')  
   }
   ```

### 2.3 Type Safety Verification

Run comprehensive type checking:
```bash
npx tsc --noEmit --strict
npm run lint
```

## Task 3: Performance Monitoring Cleanup (1 week)

### 3.1 Audit Current Performance Systems

Identify and consolidate:
- Form-level tracking
- Field-level tracking  
- Interaction-level tracking
- Web vitals tracking
- Service-level tracking

### 3.2 Streamlined Performance Hook

Replace multiple hooks with single optimized version:

```typescript
// hooks/useOptimizedPerformance.ts
interface PerformanceConfig {
  trackFormSubmits?: boolean
  trackLoadTimes?: boolean
  trackErrors?: boolean
  sampleRate?: number // 0.1 = 10% sampling
}

export function useOptimizedPerformance(config: PerformanceConfig = {}) {
  // Lightweight tracking with configurable sampling
  // Focus on actionable metrics only
  // Minimal runtime overhead
}
```

### 3.3 Performance Monitoring Guidelines

**Keep Only Essential Metrics**:
- Form submission success/failure rates
- Critical user journey timings
- Error rates and types
- Core Web Vitals (FCP, LCP, CLS)

**Remove Unnecessary Tracking**:
- Field-level interaction tracking
- Granular state change monitoring
- Non-actionable performance data

## Task 4: Testing Strategy (Throughout)

### 4.1 Component Testing

For each decomposed component:
```typescript
// __tests__/MachineBasicInfo.test.tsx
describe('MachineBasicInfo', () => {
  it('renders required fields correctly', () => {})
  it('validates input constraints', () => {})
  it('handles form submission', () => {})
})
```

### 4.2 Integration Testing

Test form composition:
```typescript
// __tests__/MachineForm.integration.test.tsx  
describe('MachineForm Integration', () => {
  it('coordinates between sub-components', () => {})
  it('maintains form state across components', () => {})
  it('handles bulk operations correctly', () => {})
})
```

### 4.3 Performance Testing

```typescript
// __tests__/performance/MachineForm.perf.test.tsx
describe('MachineForm Performance', () => {
  it('renders within acceptable time limits', () => {})
  it('handles large datasets efficiently', () => {})
  it('maintains responsiveness during bulk operations', () => {})
})
```

## Success Metrics

### Code Quality Targets
- [ ] Average component size: ≤200 lines
- [ ] Zero TypeScript strict mode errors
- [ ] Test coverage: ≥80% for new components
- [ ] Performance monitoring overhead: <5ms per interaction

### Performance Targets  
- [ ] Form load time: <500ms
- [ ] First interaction: <100ms
- [ ] Bulk operations: <2s for 100 items
- [ ] Memory usage: Stable over extended use

### Maintainability Targets
- [ ] New form components follow established patterns
- [ ] Component reusability: ≥60% shared components
- [ ] Developer onboarding: <2 days for new team members
- [ ] Feature development velocity: 25% improvement

## Risk Mitigation

### Regression Prevention
1. **Incremental refactoring** - One form at a time
2. **Feature flags** - Toggle between old/new implementations
3. **Comprehensive testing** - Before and after each refactor
4. **Performance benchmarking** - Continuous monitoring

### Quality Gates
- [ ] All tests pass before merging
- [ ] TypeScript strict mode compliance
- [ ] Performance regression detection
- [ ] Accessibility verification (axe-core)

## Completion Criteria

Phase 3 is complete when:

1. **All forms decomposed** into maintainable components (≤200 lines each)
2. **TypeScript strict mode** enabled with zero errors
3. **Performance monitoring** streamlined and optimized
4. **Test coverage** meets targets (≥80%)
5. **Documentation updated** for new component patterns
6. **Developer experience** improved (faster builds, better IntelliSense)

## Post-Completion

### Establish Patterns
- Component composition guidelines
- Performance monitoring standards  
- Testing requirements for new features
- Code review checklist for maintainability

### Knowledge Transfer
- Developer documentation for new patterns
- Component library usage guide
- Performance monitoring playbook
- Troubleshooting guide for common issues

---

**Note**: This refactor is independent of other phases and can proceed immediately. In fact, completing Phase 3 first will make security (Phase 1) and architectural (Phase 2) changes safer and easier by working with smaller, more focused components.