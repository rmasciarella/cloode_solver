# Form Component Refactoring Guide

## Overview

This guide demonstrates how to refactor large form components (600-1200+ lines) into smaller, maintainable, and accessible components using our new shared hooks and patterns.

## Refactoring Checklist

### 1. Extract Common Hooks
- [x] `useFormPerformance` - Performance tracking
- [x] `useFormData` - Data fetching with loading states
- [x] `useFormSubmission` - Form submission handling
- [x] `useFormTable` - Table/list management with filtering and sorting
- [x] `useKeyboardNavigation` - Keyboard accessibility

### 2. Create Smaller Components
- [x] Separate form fields into `*FormFields.tsx`
- [x] Extract table/list views into `*Table.tsx`
- [x] Use common `FormLayout` component
- [x] Use `FormField` wrapper for automatic ARIA attributes

### 3. Accessibility Improvements
- [x] ARIA attributes on all interactive elements
- [x] Keyboard navigation support
- [x] Focus management
- [x] Screen reader announcements
- [ ] Screen reader testing

## Before & After Example

### Before (1211 lines)
```tsx
// SkillForm.tsx - Monolithic component
export default function SkillForm() {
  // 100+ lines of state management
  // 200+ lines of data fetching
  // 100+ lines of handlers
  // 800+ lines of JSX
}
```

### After (Multiple focused files)
```tsx
// SkillFormRefactored.tsx (~200 lines)
export default function SkillFormRefactored() {
  const { trackInteraction, trackFieldFocus } = useFormPerformance('SkillForm')
  const { data: skills, loading, refresh } = useFormData({ fetchFn: skillService.getAll })
  const { handleSubmit, submitting } = useFormSubmission({ ... })
  
  return (
    <FormLayout
      title="Skill Management"
      tabs={[
        { value: 'list', label: 'View Skills', content: <SkillsTable /> },
        { value: 'create', label: 'Create Skill', content: <SkillFormFields /> },
        { value: 'bulk', label: 'Bulk Upload', content: <MassUploader /> }
      ]}
    />
  )
}

// SkillFormFields.tsx (~250 lines)
export function SkillFormFields({ form, departments, onFieldFocus }) {
  return (
    <div className="space-y-6">
      <FormSection title="Basic Information">
        <FormField id="name" label="Skill Name" required error={errors.name}>
          <Input {...register('name')} />
        </FormField>
      </FormSection>
    </div>
  )
}

// SkillsTable.tsx (~300 lines)
export function SkillsTable({ skills, onEdit, onDelete }) {
  const { data, currentPage, sortConfig, handleSort, ... } = useFormTable({ 
    data: skills,
    searchableFields: ['name', 'description']
  })
  
  return <table>...</table>
}
```

## Migration Steps

### Step 1: Analyze Current Component
```bash
# Check component size
wc -l frontend/components/forms/YourForm.tsx

# Identify patterns
grep -h "useState\|useEffect\|const fetch" YourForm.tsx
```

### Step 2: Create Directory Structure
```bash
mkdir -p frontend/components/forms/your-feature/
```

### Step 3: Extract Form Fields Component
1. Create `YourFormFields.tsx`
2. Move all form input JSX
3. Use `FormField` wrapper for accessibility
4. Pass form methods as props

### Step 4: Extract Table/List Component
1. Create `YourTable.tsx`
2. Move list/table JSX
3. Use `useFormTable` hook
4. Add sorting, filtering, pagination

### Step 5: Refactor Main Component
1. Import shared hooks
2. Replace custom implementations
3. Use `FormLayout` component
4. Connect smaller components

### Step 6: Add Keyboard Navigation
```tsx
useKeyboardNavigation({
  onEscape: () => setActiveTab('list'),
  onEnter: () => form.handleSubmit(onSubmit)()
})
```

### Step 7: Test Accessibility
1. Test with keyboard only
2. Use screen reader
3. Check ARIA attributes
4. Verify focus management

## Common Patterns to Extract

### Performance Tracking
```tsx
// Before
const performanceTracker = useRef(new FormPerformanceTracker())
// ... 50+ lines of performance code

// After
const { trackInteraction, trackFieldFocus } = useFormPerformance('FormName')
```

### Data Fetching
```tsx
// Before
const [data, setData] = useState([])
const [loading, setLoading] = useState(false)
useEffect(() => {
  // ... fetching logic
}, [])

// After
const { data, loading, refresh } = useFormData({
  fetchFn: service.getAll
})
```

### Form Submission
```tsx
// Before
const [submitting, setSubmitting] = useState(false)
const handleSubmit = async (data) => {
  // ... 30+ lines of submission logic
}

// After
const { handleSubmit, submitting } = useFormSubmission({
  onSubmit: service.create,
  onSuccess: refresh
})
```

## Benefits

1. **Reduced File Size**: 1200+ lines → 200-300 lines per file
2. **Reusability**: Shared hooks across all forms
3. **Maintainability**: Focused, single-purpose components
4. **Performance**: Standardized monitoring
5. **Accessibility**: Built-in ARIA support
6. **Type Safety**: Full TypeScript support

## Next Forms to Refactor

Priority order based on size:
1. MachineForm (925 lines)
2. SetupTimeForm (889 lines)
3. MaintenanceTypeForm (870 lines)
4. SequenceResourceForm (722 lines)
5. WorkCellForm (710 lines)

## Testing Strategy

### Unit Tests
```tsx
describe('FormFields', () => {
  it('should have proper ARIA attributes', () => {
    // Test accessibility
  })
})
```

### Integration Tests
```tsx
describe('Form Integration', () => {
  it('should submit data correctly', () => {
    // Test full flow
  })
})
```

### Accessibility Tests
```tsx
describe('Keyboard Navigation', () => {
  it('should navigate with arrow keys', () => {
    // Test keyboard support
  })
})
```