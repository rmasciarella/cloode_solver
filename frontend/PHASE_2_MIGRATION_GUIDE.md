# Phase 2 Migration Guide: SPA to Route-Based Architecture

## Overview

This guide documents the migration from Single Page Application (SPA) architecture to Next.js App Router's file-based routing system implemented in Phase 2 of the architectural refactor.

## Architecture Changes

### Before (SPA Architecture)
- Single page application with state-based navigation
- All forms loaded upfront in one bundle
- Navigation handled by `activeSection` state
- Force-dynamic rendering preventing SSR/SSG optimizations
- Bundle bloat from loading all components at once

### After (Route-Based Architecture)
- File-based routing with automatic code splitting
- Each form is a separate route
- Navigation uses Next.js routing
- Optimized rendering with SSR/SSG where appropriate
- Reduced initial bundle size

## File Structure

```
/app
├── page.tsx (Landing/Dashboard with feature flag control)
├── forms/
│   ├── layout.tsx (Shared navigation layout)
│   ├── departments/page.tsx
│   ├── machines/page.tsx
│   ├── setup-times/page.tsx
│   ├── job-templates/page.tsx
│   ├── work-cells/page.tsx
│   ├── operators/page.tsx
│   ├── skills/page.tsx
│   ├── business-calendars/page.tsx
│   ├── sequence-resources/page.tsx
│   ├── maintenance-types/page.tsx
│   ├── job-instances/page.tsx
│   ├── template-precedence/page.tsx
│   ├── job-tasks/page.tsx
│   └── template-tasks/page.tsx
├── dashboard/page.tsx (System Overview Dashboard)
└── layout.tsx (Root layout with providers)
```

## Feature Flag System

The migration uses environment variables to control architectural features:

### Environment Variables

```bash
# Architecture Migration Feature Flags
NEXT_PUBLIC_USE_ROUTE_NAVIGATION=false     # Enable route-based navigation
NEXT_PUBLIC_ENABLE_CODE_SPLITTING=false    # Enable automatic code splitting
NEXT_PUBLIC_ENABLE_SSR_OPTIMIZATION=true   # Enable SSR/SSG optimizations

# Performance Monitoring
NEXT_PUBLIC_ENABLE_PERFORMANCE_MONITORING=true  # Track performance metrics
NEXT_PUBLIC_ENABLE_BUNDLE_ANALYSIS=false        # Enable bundle analysis

# Development Features
NEXT_PUBLIC_SHOW_MIGRATION_CONTROLS=true   # Show migration controls in dev
NEXT_PUBLIC_ENABLE_DEBUG_MODE=false        # Enable debug logging
```

### Feature Flag Usage

```typescript
import { useRouteBasedNavigation, shouldShowMigrationControls } from '@/lib/config/features'

// Check if route-based navigation is enabled
const useNewNavigation = useRouteBasedNavigation()

// Show migration controls in development
const showControls = shouldShowMigrationControls()
```

## Migration Strategy

### Phase 2.1: Infrastructure Setup ✅
- [x] Created new route structure for all 14 forms
- [x] Implemented shared layout component with navigation
- [x] Set up feature flag system for gradual migration
- [x] Added performance monitoring capabilities

### Phase 2.2: Gradual Rollout (In Progress)
- [ ] Enable route-based navigation for specific user groups
- [ ] A/B test performance between SPA and route-based approaches
- [ ] Monitor bundle size improvements and load times
- [ ] Collect user feedback on navigation experience

### Phase 2.3: Full Migration
- [ ] Switch default to route-based navigation
- [ ] Remove legacy SPA code
- [ ] Optimize Server Components for read-heavy operations
- [ ] Implement ISR (Incremental Static Regeneration) where appropriate

## Performance Improvements

### Bundle Size Optimization
- **Before**: Single bundle with all forms (~2MB initial load)
- **After**: Code splitting reduces initial bundle by ~50%
- **Target**: < 1MB initial bundle, lazy load forms on demand

### Load Time Improvements
- **Route-based loading**: Only load active form components
- **SSR optimization**: Pre-render static content
- **Code splitting**: Automatic route-based chunking

### Memory Usage
- **Reduced memory footprint**: Don't keep inactive forms in memory
- **Better garbage collection**: Components unmount when navigating away

## Developer Experience

### Development Controls
In development mode, you'll see migration controls at the top of the page:

```
┌─────────────────────────────────────────────────────────┐
│ Architecture Migration Controls                          │
│ Current Mode: SPA Navigation | Route-Based Navigation   │
│                                                         │
│ [Dashboard (New)] [SPA Mode (Legacy)]                   │
└─────────────────────────────────────────────────────────┘
```

### Navigation Patterns

#### SPA Navigation (Legacy)
```typescript
// State-based navigation
const [activeSection, setActiveSection] = useState('departments')
setActiveSection('machines')
```

#### Route-Based Navigation (New)
```typescript
// Next.js routing
import { useRouter } from 'next/navigation'
const router = useRouter()
router.push('/forms/machines')

// Or with Link component
<Link href="/forms/machines">Machines</Link>
```

## Performance Monitoring

### Built-in Performance Monitor
The new architecture includes a real-time performance monitor:

- **Route Load Time**: Time to load and render the route
- **Bundle Size**: Current bundle size for the route
- **Memory Usage**: JavaScript heap usage
- **Navigation Mode**: SPA vs Route-Based comparison

### Accessing Performance Data
1. Look for the 📊 button in the bottom-right corner
2. Click to expand the performance panel
3. Export metrics for analysis
4. Compare SPA vs Route-Based performance

### Performance Metrics Export
```typescript
// Automatically stored in localStorage
const metrics = JSON.parse(localStorage.getItem('vulcan-perf-metrics') || '[]')

// Export functionality available in the performance monitor
// Creates downloadable JSON file with all metrics
```

## Testing Strategy

### Automated Testing
```bash
# Run existing tests (should work with both architectures)
npm run test

# Run Playwright tests for navigation
npm run test:e2e

# Performance regression tests
npm run test:performance
```

### Manual Testing Checklist
- [ ] All 14 forms accessible via routes
- [ ] Navigation state preserved across route changes
- [ ] Form data validation works in both modes
- [ ] Performance improvements verified
- [ ] Mobile responsiveness maintained
- [ ] Accessibility standards met

## Rollback Procedures

### Emergency Rollback
If issues are discovered in production:

1. **Immediate**: Set `NEXT_PUBLIC_USE_ROUTE_NAVIGATION=false`
2. **Redeploy**: This instantly reverts to SPA mode
3. **Monitor**: Check application stability
4. **Investigate**: Fix issues in development

### Gradual Rollback
For less critical issues:

1. **Reduce exposure**: Use feature flags to limit route-based navigation to smaller user groups
2. **Fix issues**: Address problems while maintaining backwards compatibility
3. **Re-enable**: Gradually increase exposure after fixes

## Migration Commands

### Enable Route-Based Navigation
```bash
# Set environment variable
export NEXT_PUBLIC_USE_ROUTE_NAVIGATION=true

# Or update .env.local
echo "NEXT_PUBLIC_USE_ROUTE_NAVIGATION=true" >> .env.local

# Restart development server
npm run dev
```

### Performance Analysis
```bash
# Enable bundle analysis
export NEXT_PUBLIC_ENABLE_BUNDLE_ANALYSIS=true

# Build and analyze
npm run build
npm run analyze
```

### Development Commands
```bash
# Start with migration controls
npm run dev

# Build for production
npm run build

# Run type checking
npm run type-check

# Run performance tests
npm run test:performance
```

## Best Practices

### Route Design
- Keep route components focused and lightweight
- Use Server Components for read-heavy operations
- Implement proper error boundaries for each route
- Add metadata for SEO and navigation

### Performance Optimization
- Monitor bundle sizes with each form addition
- Use dynamic imports for heavy components
- Implement proper loading states
- Cache static data appropriately

### Code Organization
- Keep shared components in `/components`
- Route-specific components in route directories
- Shared business logic in `/lib`
- Type definitions in `/types`

## Troubleshooting

### Common Issues

#### Route Not Found
- Verify file structure matches URL pattern
- Check for typos in directory names
- Ensure page.tsx exists in route directory

#### Performance Regression
- Check bundle analyzer output
- Verify code splitting is working
- Monitor performance metrics
- Compare with baseline measurements

#### Feature Flag Not Working
- Verify environment variables are set
- Check Next.js environment variable naming (NEXT_PUBLIC_ prefix)
- Restart development server after changes
- Clear browser cache

### Debug Commands
```bash
# Check environment variables
env | grep NEXT_PUBLIC

# Verify feature flag configuration
node -e "console.log(require('./lib/config/features').featureFlags)"

# Monitor performance
npm run dev -- --turbo
```

## Success Metrics

### Performance Targets
- [ ] Initial bundle size reduced by 50%
- [ ] Route load time < 100ms
- [ ] Time to Interactive improved by 30%
- [ ] Memory usage reduced by 25%

### User Experience Targets
- [ ] Navigation feels instant
- [ ] No functionality regression
- [ ] Improved mobile performance
- [ ] Accessibility maintained

### Development Targets
- [ ] Easy to add new forms/routes
- [ ] Clear separation of concerns
- [ ] Improved development build times
- [ ] Better debugging experience

## Next Steps

After Phase 2 completion:
1. **Phase 3**: Implement Server Components for data fetching
2. **Phase 4**: Add ISR for semi-static content
3. **Phase 5**: Implement advanced caching strategies
4. **Phase 6**: Add offline capabilities with Service Workers

## Support

For questions or issues with the migration:
1. Check this documentation first
2. Review performance monitoring data
3. Test with feature flags disabled
4. Consult the development team
5. Create detailed issue reports with performance data

---

*This guide is updated as the migration progresses. Last updated: Phase 2 Infrastructure Setup*