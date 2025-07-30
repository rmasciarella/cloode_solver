# Code Generation Templates for OR-Tools

## Centralized Type Aliases for OR-Tools

### Standard Type Definitions
Import these in all constraint and solver files for consistent typing:

```python
# Required imports for type safety
from typing import Dict, List, Tuple, Optional, Union
from ortools.sat.python import cp_model

# Core type aliases - use throughout the project
TaskKey = Tuple[str, str]  # (job_id, task_id)
MachineKey = str
AssignmentKey = Tuple[str, str, str]  # (job_id, task_id, machine_id)

# Variable collections with proper OR-Tools types
TaskStartDict = Dict[TaskKey, cp_model.IntVar]
TaskEndDict = Dict[TaskKey, cp_model.IntVar]
TaskDurationDict = Dict[TaskKey, cp_model.IntVar]
TaskIntervalDict = Dict[TaskKey, cp_model.IntervalVar]
TaskAssignmentDict = Dict[AssignmentKey, cp_model.IntVar]  # BoolVar is IntVar {0,1}
MachineIntervalDict = Dict[MachineKey, List[cp_model.IntervalVar]]

# Problem data types
PrecedenceList = List[Tuple[TaskKey, TaskKey]]
SetupTimeDict = Dict[AssignmentKey, int]  # Setup time in time units
```

### Usage Example
```python
# Import centralized types at top of constraint files
from .types import TaskStartDict, TaskEndDict, TaskKey, PrecedenceList

def add_precedence_constraints(
    model: cp_model.CpModel,
    task_starts: TaskStartDict,
    task_ends: TaskEndDict,
    precedences: PrecedenceList
) -> None:
    """Constraint function using centralized types."""
    # Implementation...
```

## Constraint Function Template

```python
def add_{constraint_type}_constraints(
    model: cp_model.CpModel,
    {required_variables}: TaskStartDict,  # Use centralized type aliases
    {additional_params}: {param_types}
) -> None:
    """Add {constraint_type} constraints to the model.
    
    Mathematical formulation:
        {mathematical_formula}
    
    Business logic:
        {business_explanation}
    
    Args:
        model: The CP-SAT model to add constraints to
        {param_name}: {param_description}
        
    Constraints added:
        - {constraint_1_description}
        - {constraint_2_description}
    
    Performance considerations:
        - {performance_note_1}
        - {performance_note_2}
    """
    # Implementation (max 30 lines)
    for {iteration_vars} in {iteration_target}:
        # Add constraint
        model.Add({constraint_expression})
        
        # Add redundant constraints if helpful
        if {condition_for_redundancy}:
            model.Add({redundant_constraint})
```

## Unit Test Template

```python
def test_{constraint_name}_constraints():
    """Test that {constraint_name} constraints are correctly enforced."""
    # GIVEN: A model with test data
    model = cp_model.CpModel()
    
    # Create required variables
    {variable_name} = {
        {test_key}: model.NewIntVar({min_bound}, {max_bound}, '{var_name}')
        for {test_key} in {test_data}
    }
    
    # WHEN: Adding the constraint
    add_{constraint_name}_constraints(
        model=model,
        {param_name}={test_param_value}
    )
    
    # THEN: Solver finds valid solution meeting constraint
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
    
    # Verify constraint is satisfied
    {assertion_checks}
    
def test_{constraint_name}_constraints_edge_case():
    """Test {constraint_name} with edge case: {edge_case_description}."""
    # Test implementation for edge cases
```

## Integration Test Template

```python
def test_phase_{phase_num}_integration():
    """Test Phase {phase_num} constraints work together correctly."""
    # GIVEN: A complete problem setup
    problem = create_test_problem(
        num_jobs={test_jobs},
        num_tasks_per_job={test_tasks},
        num_machines={test_machines}
    )
    
    # WHEN: Solving with all Phase {phase_num} constraints
    solver = FreshSolver()
    solution = solver.solve(problem)
    
    # THEN: Solution is valid and meets performance targets
    assert solution is not None
    assert solution.solve_time < {performance_target}
    
    # Verify all constraints are satisfied
    assert_precedences_respected(solution, problem.precedences)
    assert_no_task_overlap(solution)
    assert_all_tasks_scheduled(solution, problem.tasks)
    
    # Verify solution quality
    assert solution.makespan <= {expected_makespan}
```

## Data Model Template

```python
@dataclass
class {ModelName}:
    """Represents {model_description}.
    
    Attributes:
        {attribute_name}: {attribute_description}
    """
    {attribute_name}: {attribute_type}
    {attribute_name_2}: {attribute_type_2} = field(default_factory={factory})
    
    def __post_init__(self):
        """Validate {model_name} data after initialization."""
        # Validate required fields
        if not self.{required_field}:
            raise ValueError(f"{ModelName} must have {required_field}")
            
        # Validate business rules
        if self.{numeric_field} <= 0:
            raise ValueError(
                f"{ModelName} {numeric_field} must be positive: "
                f"{self.{numeric_field}}"
            )
            
        # Convert units if needed
        if hasattr(self, '{time_field}_minutes'):
            self.{time_field}_units = minutes_to_time_units(
                self.{time_field}_minutes
            )
```

## Variable Creation Template

```python
def create_{variable_type}_variables(
    model: cp_model.CpModel,
    {data_source}: {data_type}
) -> Dict[{key_type}, {var_type}]:
    """Create {variable_type} decision variables.
    
    Args:
        model: The CP-SAT model
        {data_source}: {data_description}
        
    Returns:
        Dictionary mapping {key_description} to {variable_description}
    """
    {variable_dict} = {}
    
    for {item} in {data_source}:
        # Calculate tight bounds
        min_bound = {calculate_min_bound}
        max_bound = {calculate_max_bound}
        
        # Create variable with descriptive name
        var_name = f"{variable_prefix}_{{{item_id_fields}}}"
        {variable_dict}[{key}] = model.NewIntVar(
            min_bound, max_bound, var_name
        )
    
    return {variable_dict}
```

## Objective Function Template

```python
def set_{objective_type}_objective(
    model: cp_model.CpModel,
    {required_variables}: Dict[{key_type}, {var_type}],
    {weights}: Optional[Dict[{key_type}, int]] = None
) -> None:
    """Set {objective_type} as the optimization objective.
    
    Objective formulation:
        {objective_formula}
        
    Args:
        model: The CP-SAT model
        {required_variables}: {variable_description}
        {weights}: Optional weights for weighted objectives
    """
    # Create objective variable if needed
    objective_var = model.NewIntVar(
        {obj_min_bound}, {obj_max_bound}, '{objective_name}'
    )
    
    # Define objective
    if {objective_type} == 'minimize_makespan':
        # Makespan = max(all task end times)
        model.AddMaxEquality(
            objective_var,
            [var for var in {required_variables}.values()]
        )
    elif {objective_type} == 'weighted_sum':
        # Weighted sum of components
        model.Add(
            objective_var == sum(
                {weights}.get(key, 1) * var
                for key, var in {required_variables}.items()
            )
        )
    
    # Set optimization direction
    model.{Minimize_or_Maximize}(objective_var)
```

## Search Strategy Template

```python
def add_{strategy_type}_search_strategy(
    model: cp_model.CpModel,
    {priority_variables}: List[IntVar],
    {secondary_variables}: Optional[List[IntVar]] = None
) -> None:
    """Add {strategy_type} search strategy to guide solver.
    
    Strategy:
        {strategy_description}
        
    Args:
        model: The CP-SAT model
        {priority_variables}: Variables to assign first
        {secondary_variables}: Variables to assign after priority
    """
    # Primary decision strategy
    model.AddDecisionStrategy(
        {priority_variables},
        cp_model.{variable_selection_strategy},
        cp_model.{value_selection_strategy}
    )
    
    # Secondary strategy if provided
    if {secondary_variables}:
        model.AddDecisionStrategy(
            {secondary_variables},
            cp_model.CHOOSE_FIRST,
            cp_model.SELECT_MIN_VALUE
        )
```

## Solver Configuration Template

```python
def configure_solver_for_{problem_type}(
    solver: cp_model.CpSolver,
    time_limit_seconds: int = {default_time_limit},
    num_workers: int = {default_workers}
) -> None:
    """Configure solver parameters for {problem_type} problems.
    
    Args:
        solver: The CP-SAT solver instance
        time_limit_seconds: Maximum solve time
        num_workers: Number of parallel workers
    """
    # Time limit
    solver.parameters.max_time_in_seconds = time_limit_seconds
    
    # Parallelism
    solver.parameters.num_search_workers = num_workers
    
    # Problem-specific parameters
    if {problem_characteristic}:
        solver.parameters.{parameter_name} = {parameter_value}
        
    # Logging for debugging
    if {debug_mode}:
        solver.parameters.log_search_progress = True
        solver.log_callback = lambda msg: logger.debug(f"Solver: {msg}")
```

## Solution Extraction Template

```python
def extract_{solution_type}_solution(
    solver: cp_model.CpSolver,
    {variables}: Dict[{key_type}, {var_type}],
    problem: SchedulingProblem
) -> {SolutionType}:
    """Extract {solution_type} from solved model.
    
    Args:
        solver: The solved CP-SAT solver
        {variables}: Decision variables
        problem: Original problem data
        
    Returns:
        {SolutionType} containing {solution_contents}
    """
    if solver.StatusName() not in ['OPTIMAL', 'FEASIBLE']:
        return None
        
    # Extract variable values
    {extracted_values} = {}
    for key, var in {variables}.items():
        {extracted_values}[key] = solver.Value(var)
    
    # Build solution object
    solution = {SolutionType}(
        {field_name}={build_field_value},
        solve_time=solver.WallTime(),
        objective_value=solver.ObjectiveValue(),
        status=solver.StatusName()
    )
    
    # Add computed fields
    solution.{computed_field} = {compute_from_values}
    
    return solution
```

## Performance Profiling Template

```python
def profile_{operation}_performance(
    problem: SchedulingProblem,
    {config_params}: Dict[str, Any]
) -> PerformanceMetrics:
    """Profile performance of {operation}.
    
    Measures:
        - {metric_1}
        - {metric_2}
        - {metric_3}
    """
    metrics = PerformanceMetrics()
    
    # Measure variable creation
    start_time = time.time()
    {variables} = create_{variable_type}_variables(model, problem)
    metrics.variable_creation_time = time.time() - start_time
    metrics.variable_count = len({variables})
    
    # Measure constraint addition
    start_time = time.time()
    add_{constraint_type}_constraints(model, {variables})
    metrics.constraint_time = time.time() - start_time
    
    # Measure solving
    start_time = time.time()
    status = solver.Solve(model)
    metrics.solve_time = time.time() - start_time
    
    # Record solution quality
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        metrics.objective_value = solver.ObjectiveValue()
        metrics.solution_found = True
    
    return metrics
```

## Error Handling Template

```python
def {operation}_with_validation(
    {parameters}: {param_types}
) -> {return_type}:
    """Perform {operation} with comprehensive error handling.
    
    Args:
        {parameters}: {param_descriptions}
        
    Returns:
        {return_description}
        
    Raises:
        ValueError: If {invalid_condition}
        RuntimeError: If {runtime_error_condition}
    """
    # Input validation
    if not {valid_condition}:
        raise ValueError(
            f"{operation}: {parameter} is invalid: {parameter_value}. "
            f"Expected: {expected_condition}"
        )
    
    try:
        # Main operation
        result = {perform_operation}
        
        # Validate result
        if not {result_valid_condition}:
            raise RuntimeError(
                f"{operation} produced invalid result: {result}"
            )
            
        return result
        
    except Exception as e:
        logger.error(f"{operation} failed: {e}")
        # Add context to error
        raise RuntimeError(
            f"{operation} failed with {parameters}: {e}"
        ) from e
```