# Product Requirements Document: OR-Tools Production Scheduling Solver

## Executive Summary

This PRD outlines the requirements for evolving the existing OR-Tools CP-SAT scheduling solver from its current state (Phase 2.5) to a production-ready system. The solver will enable manufacturers to optimize job scheduling across machines, resources, and operators while meeting business constraints and objectives.

## Product Vision

Create a robust, scalable scheduling optimization system that transforms manufacturing operations by intelligently allocating resources, minimizing production time, and reducing costs while respecting all operational constraints.

## Current State (Phase 0 & Phase 1 Complete)

The system currently provides:
- Basic job-shop scheduling with machine assignment
- Multi-mode task execution (different machines/durations)
- Precedence constraint handling
- Database integration with Supabase
- 15-minute time interval granularity
- **✅ High-capacity machine support (Phase 1.1 completed)**
  - Machines with capacity > 1 allowing concurrent jobs
  - Visual indication of concurrent tasks using lane assignment
  - Capacity validation and cumulative constraints
- **✅ Setup time constraints (Phase 1.2 completed)**
  - Sequence-dependent setup times between tasks
  - Configurable per task pair and machine
  - Integrated into solver with conditional constraints
  - Setup time visualization as gold blocks on Gantt chart
  - Comprehensive setup time metrics and statistics
- **✅ Comprehensive test coverage (96% overall)**
  - All core solver modules tested
  - Performance regression tests established
  - Continuous integration ready

## Business Objectives

1. **Reduce Production Time**: Minimize makespan by 20-30% compared to manual scheduling
2. **Optimize Resource Utilization**: Achieve 85%+ machine utilization rates
3. **Meet Delivery Commitments**: Ensure 95%+ on-time delivery through deadline awareness
4. **Reduce Operational Costs**: Optimize for cost-efficiency in resource allocation
5. **Enable Real-time Adaptability**: Support schedule updates within 5 minutes
6. **Maximize Equipment Utilization**: Strategic weekend scheduling for long unattended processes (24-72 hours)
7. **Enforce Physical Constraints**: Respect WorkCell capacity limits for space, utilities, and safety

## User Personas

### 1. Production Planner
- **Goal**: Create optimal daily/weekly production schedules
- **Pain Points**: Manual scheduling is time-consuming and suboptimal
- **Needs**: Quick schedule generation, visual feedback, constraint validation

### 2. Shop Floor Supervisor
- **Goal**: Execute schedules and handle real-time changes
- **Pain Points**: Disruptions require manual rescheduling
- **Needs**: Real-time updates, resource availability visibility

### 3. Operations Manager
- **Goal**: Monitor KPIs and optimize overall efficiency
- **Pain Points**: Limited visibility into optimization potential
- **Needs**: Performance metrics, cost analysis, what-if scenarios

### 4. System Administrator
- **Goal**: Maintain and configure the scheduling system
- **Pain Points**: Complex constraint management
- **Needs**: Easy configuration, monitoring tools, integration APIs

## Functional Requirements by Phase

### Phase 0: Cleanup and Stabilization (Sprint 1) - ✅ COMPLETE

**Objective**: Establish solid foundation for new features

**User Stories**:
1. As a developer, I need comprehensive test coverage so that new features don't break existing functionality
   - **Acceptance Criteria**:
     - [x] 90%+ test coverage for core solver modules (achieved 96%)
     - [x] All constraints have unit tests (including new setup times)
     - [x] Performance regression tests established

2. As a system admin, I need clear documentation to understand system capabilities
   - **Acceptance Criteria**:
     - [x] Updated architecture documentation (CLAUDE.md system)
     - [x] Constraint pattern library documented (CONSTRAINT_PATTERNS.md)
     - [x] Solver usage documentation (README.md, CLAUDE.md)

### Phase 1: Enhanced Machine Constraints (Sprint 2-3) - ✅ COMPLETE

**Objective**: Support real-world machine capabilities and constraints

**User Stories**:
1. As a production planner, I need to schedule multiple jobs on high-capacity machines - ✅ COMPLETE
   - **Acceptance Criteria**:
     - [x] Support machines with capacity > 1
     - [x] Visual indication of concurrent jobs
     - [x] Capacity validation in UI

2. As a production planner, I need to account for setup times between different products - ✅ COMPLETE
   - **Acceptance Criteria**:
     - [x] Configurable setup time matrix
     - [x] Setup times reflected in schedule
     - [x] Total setup time metrics (UI/reporting complete)

3. As a production planner, I need to schedule unattended tasks that can run outside business hours - **CRITICAL**
   - **Acceptance Criteria**:
     - [ ] Unattended tasks require operator setup during business hours (Mon-Fri 7am-4pm)
     - [ ] Machine execution continues 24/7 after setup for unattended tasks
     - [ ] Strategic scheduling of long tasks (24+ hours) to utilize weekends
     - [ ] Dual resource modeling: labor setup + machine execution intervals
     - [ ] Performance optimization for 72-hour processes

4. As a shop floor supervisor, I need to enforce WorkCell capacity limits for physical locations
   - **Acceptance Criteria**:
     - [ ] WorkCell capacity constraints independent of individual machine availability
     - [ ] Maximum simultaneous machines per WorkCell enforced
     - [ ] Integration with existing machine assignment constraints
     - [ ] Support for shared utilities and space limitations per WorkCell

~~5. As a shop floor supervisor, I need to respect machine maintenance windows~~ - **DESCOPED**
   - *Rationale: Not required for current use case; maintenance windows were not part of the original model*

### Phase 2: Resource and Skill Constraints (Sprint 4-5)

**Objective**: Integrate human resources and skill requirements

**User Stories**:
1. As a production planner, I need to assign operators with required skills to tasks
   - **Acceptance Criteria**:
     - [ ] Skill requirement definition per task
     - [ ] Operator skill matrix management
     - [ ] Automatic skill matching

2. As a shop floor supervisor, I need to ensure operator availability matches task requirements
   - **Acceptance Criteria**:
     - [ ] Operator shift calendar integration
     - [ ] Multi-resource task support (machine + operator)
     - [ ] Resource conflict resolution

3. As an operations manager, I need to track operator utilization
   - **Acceptance Criteria**:
     - [ ] Operator utilization reports
     - [ ] Skill gap analysis
     - [ ] Overtime prediction

### Phase 3: Advanced Scheduling Features (Sprint 6-7)

**Objective**: Implement sophisticated scheduling capabilities

**User Stories**:
1. As a production planner, I need multi-objective optimization beyond just makespan
   - **Acceptance Criteria**:
     - [ ] Configurable objective weights (time, cost, lateness)
     - [ ] Pareto-optimal solution options
     - [ ] Trade-off visualization

2. As a production planner, I need to handle rush orders through task preemption
   - **Acceptance Criteria**:
     - [ ] Define preemptible tasks
     - [ ] Automatic rescheduling for urgent orders
     - [ ] Preemption cost calculation

3. As an operations manager, I need to ensure on-time delivery
   - **Acceptance Criteria**:
     - [ ] Due date constraint enforcement
     - [ ] Lateness penalty calculation
     - [ ] Delivery performance metrics

4. As a shop floor supervisor, I need WIP limits to prevent bottlenecks
   - **Acceptance Criteria**:
     - [ ] Configurable WIP limits per work cell
     - [ ] Real-time WIP monitoring
     - [ ] Automatic flow balancing

### Phase 4: Production Features (Sprint 8-9)

**Objective**: Enable production deployment and operations

**User Stories**:
1. As a system admin, I need persistent storage of schedules and results
   - **Acceptance Criteria**:
     - [ ] Schedule version history
     - [ ] Result comparison tools
     - [ ] Audit trail for changes

2. As a shop floor supervisor, I need incremental rescheduling for disruptions
   - **Acceptance Criteria**:
     - [ ] Partial schedule updates < 30 seconds
     - [ ] Minimal disruption to running tasks
     - [ ] Change impact visualization

3. As an operations manager, I need real-time monitoring of schedule execution
   - **Acceptance Criteria**:
     - [ ] Live schedule status dashboard
     - [ ] KPI tracking (OEE, utilization, delays)
     - [ ] Alert system for deviations

### Phase 5: API Layer (Sprint 10)

**Objective**: Enable system integration and external access

**User Stories**:
1. As a system integrator, I need REST APIs to integrate with ERP/MES systems
   - **Acceptance Criteria**:
     - [ ] Complete REST API for all operations
     - [ ] OpenAPI specification
     - [ ] Rate limiting and authentication

2. As a developer, I need GraphQL for flexible data queries
   - **Acceptance Criteria**:
     - [ ] GraphQL endpoint with full schema
     - [ ] Subscription support for real-time updates
     - [ ] Query optimization

3. As a production system, I need webhooks for schedule events
   - **Acceptance Criteria**:
     - [ ] Configurable webhook endpoints
     - [ ] Event filtering options
     - [ ] Retry mechanism for failures

### Phase 6: Advanced Solver Strategies (Sprint 11)

**Objective**: Optimize solver performance for large-scale problems

**User Stories**:
1. As a production planner, I need fast solutions for large scheduling problems
   - **Acceptance Criteria**:
     - [ ] Custom search strategies for problem types
     - [ ] Solution quality vs. time trade-offs
     - [ ] Parallel solving capabilities

2. As a power user, I need to guide the solver with domain knowledge
   - **Acceptance Criteria**:
     - [ ] Solution hint interface
     - [ ] Manual constraint relaxation
     - [ ] Solver parameter tuning UI

## Non-Functional Requirements

### Performance
- **Small datasets** (50 tasks): < 10 seconds solve time
- **Medium datasets** (500 tasks): < 60 seconds solve time
- **Large datasets** (5000 tasks): < 30 minutes solve time
- **API response time**: < 200ms for queries, < 5s for solve requests

### Scalability
- Support up to 10,000 concurrent API requests
- Handle datasets with 50,000+ tasks
- Horizontal scaling for solver instances

### Reliability
- 99.9% uptime for API services
- Automatic failover for solver instances
- Data consistency guarantees

### Security
- JWT-based authentication
- Role-based access control (RBAC)
- Audit logging for all operations
- Encrypted data at rest and in transit

### Usability
- Intuitive constraint configuration
- Clear error messages with resolution hints
- Progressive disclosure of advanced features
- Multi-language support (initially English)

## Success Metrics

### Phase 0-1 (Weeks 1-2) - ✅ COMPLETE
- ✅ Test coverage > 90% (achieved 96% overall coverage)
- ✅ Performance baseline established (regression tests created)
- ✅ High-capacity machine support (completed with visual lane assignment)
- ✅ Setup time constraints working (completed with full UI visualization)
- ✅ Documentation system established (CLAUDE.md)

### Phase 1.3-1.4 (Weeks 3-4) - CRITICAL EXTENSIONS
- [ ] Unattended task constraints operational (business hours setup, 24/7 execution)
- [ ] WorkCell capacity limits enforced (physical location constraints)
- [ ] Weekend scheduling optimization for long processes (24+ hour tasks)
- [ ] Dual resource modeling functional (labor + machine intervals)

### Phase 2-3 (Weeks 3-5)
- Skill-based scheduling operational
- Multi-objective optimization functional
- 20% makespan improvement demonstrated

### Phase 4-6 (Weeks 6-8)
- Production deployment successful
- API integration with 1+ external system
- < 60s solve time for 500-task problems

### Long-term (3 months)
- 95% on-time delivery rate
- 85% resource utilization
- 30% reduction in scheduling time
- 5+ active production deployments

## Technical Constraints

1. **OR-Tools CP-SAT**: Must use Google OR-Tools as the core solver
2. **Python**: Backend implementation in Python 3.8+
3. **Supabase**: PostgreSQL database via Supabase
4. **Time Granularity**: 15-minute intervals for all scheduling
5. **Business Hours**: Standard operating hours Mon-Fri 7am-4pm for operator availability
6. **Dual Resource Modeling**: Unattended tasks require both labor (setup) and machine (execution) resources
7. **WorkCell Physical Limits**: Machine capacity constrained by physical workspace limitations

## Dependencies

1. **External Systems**:
   - ERP system for job/order data
   - MES for shop floor feedback
   - HR system for operator availability

2. **Infrastructure**:
   - PostgreSQL database
   - Redis for caching
   - Container orchestration platform

## Risks and Mitigation

### Technical Risks
1. **Solver Performance**
   - *Risk*: Large problems may exceed time limits
   - *Mitigation*: Implement problem decomposition strategies

2. **Integration Complexity**
   - *Risk*: External system APIs may be unreliable
   - *Mitigation*: Implement robust retry and caching mechanisms

### Business Risks
1. **User Adoption**
   - *Risk*: Users resist change from manual processes
   - *Mitigation*: Phased rollout with training program

2. **Data Quality**
   - *Risk*: Poor input data leads to suboptimal schedules
   - *Mitigation*: Data validation and cleansing pipeline

## Implementation Timeline

- **Week 1**: Phase 0 - Cleanup and stabilization
- **Week 2-3**: Phase 1 - Enhanced machine constraints
- **Week 3-4**: Phase 2 - Resource and skill constraints
- **Week 5-6**: Phase 3 - Advanced scheduling features
- **Week 6-7**: Phase 4 - Production features
- **Week 7-8**: Phase 5 - API layer
- **Week 8**: Phase 6 - Advanced solver strategies

## Appendix

### A. Glossary
- **CP-SAT**: Constraint Programming with Boolean Satisfiability
- **Makespan**: Total time to complete all jobs
- **WIP**: Work In Progress
- **OEE**: Overall Equipment Effectiveness

### B. Related Documents
- IMPLEMENTATION_PLAN_V2.md
- CONSTRAINT_PATTERNS.md
- STANDARDS.md
- CLAUDE.md

### C. Open Questions
1. Integration requirements with specific ERP/MES systems?
2. Specific industry regulations to consider?
3. Multi-site scheduling requirements?
4. Mobile interface requirements?