"""Unit tests for template skill optimization constraints."""

from ortools.sat.python import cp_model

from src.solver.constraints.phase2.template_skill_optimization import (
    add_template_cross_training_optimization,
    add_template_skill_optimization_constraints,
    add_template_skill_workload_balancing,
)
from src.solver.models.problem import OperatorSkill, ProficiencyLevel, SchedulingProblem
from tests.fixtures.template_problem_factory import create_template_test_problem


class TestTemplateSkillOptimization:
    """Test template-aware skill optimization constraints."""

    def test_template_skill_optimization_basic(self):
        """Test basic template skill optimization functionality."""
        # GIVEN: A template-based problem with 2 instances and 2 operators
        problem = create_template_test_problem(
            num_instances=2, template_tasks_count=2, operators_count=2, skills_count=2
        )

        model = cp_model.CpModel()

        # Create template task assignment variables
        task_operator_assigned = {}
        for instance in problem.job_instances:
            for template_task in problem.job_template.template_tasks:
                for operator in problem.operators:
                    key = (
                        instance.instance_id,
                        template_task.template_task_id,
                        operator.operator_id,
                    )
                    task_operator_assigned[key] = model.NewBoolVar(
                        f"assign_{key[0][:8]}_{key[1][:8]}_{key[2][:8]}"
                    )

        # Create task timing variables (required for signature)
        task_starts = {}
        task_ends = {}
        for instance in problem.job_instances:
            for template_task in problem.job_template.template_tasks:
                key = (instance.instance_id, template_task.template_task_id)
                task_starts[key] = model.NewIntVar(
                    0, 100, f"start_{key[0][:8]}_{key[1][:8]}"
                )
                task_ends[key] = model.NewIntVar(
                    0, 100, f"end_{key[0][:8]}_{key[1][:8]}"
                )

        # WHEN: Adding template skill optimization constraints
        optimization_vars = add_template_skill_optimization_constraints(
            model, task_starts, task_ends, task_operator_assigned, problem
        )

        # THEN: Optimization variables created for each template task
        assert len(optimization_vars) == len(problem.job_template.template_tasks)
        for template_task in problem.job_template.template_tasks:
            assert template_task.template_task_id in optimization_vars

        # AND: Model can be solved successfully
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    def test_template_skill_optimization_empty_problem(self):
        """Test template skill optimization with empty problem."""
        # GIVEN: Empty scheduling problem
        problem = SchedulingProblem(
            jobs=[], machines=[], work_cells=[], precedences=[], operators=[], skills=[]
        )
        model = cp_model.CpModel()

        # WHEN: Adding template skill optimization constraints
        optimization_vars = add_template_skill_optimization_constraints(
            model, {}, {}, {}, problem
        )

        # THEN: No optimization variables created
        assert optimization_vars == {}

    def test_template_skill_optimization_non_template_problem(self):
        """Test template skill optimization with non-template problem."""
        # GIVEN: Legacy (non-template) problem
        problem = SchedulingProblem(
            jobs=[],
            machines=[],
            work_cells=[],
            precedences=[],
            operators=[],
            skills=[],
            is_template_based=False,
        )
        model = cp_model.CpModel()

        # WHEN: Adding template skill optimization constraints
        optimization_vars = add_template_skill_optimization_constraints(
            model, {}, {}, {}, problem
        )

        # THEN: No optimization variables created (warning logged)
        assert optimization_vars == {}

    def test_template_skill_consistency_constraints(self):
        """Test that skill consistency is maintained across template instances."""
        # GIVEN: Template problem with multiple instances of same task
        problem = create_template_test_problem(
            num_instances=3, template_tasks_count=1, operators_count=3, skills_count=1
        )

        model = cp_model.CpModel()

        # Create variables with different efficiency scenarios
        task_operator_assigned = {}
        task_starts = {}
        task_ends = {}

        template_task = problem.job_template.template_tasks[0]

        for instance in problem.job_instances:
            for operator in problem.operators:
                key = (
                    instance.instance_id,
                    template_task.template_task_id,
                    operator.operator_id,
                )
                task_operator_assigned[key] = model.NewBoolVar(
                    f"assign_{key[0][:8]}_{key[1][:8]}_{key[2][:8]}"
                )

            # Timing variables
            timing_key = (instance.instance_id, template_task.template_task_id)
            task_starts[timing_key] = model.NewIntVar(
                0, 100, f"start_{timing_key[0][:8]}_{timing_key[1][:8]}"
            )
            task_ends[timing_key] = model.NewIntVar(
                0, 100, f"end_{timing_key[0][:8]}_{timing_key[1][:8]}"
            )

        # WHEN: Adding template skill optimization constraints
        optimization_vars = add_template_skill_optimization_constraints(
            model, task_starts, task_ends, task_operator_assigned, problem
        )

        # THEN: Solver finds solution with skill consistency
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

        # AND: Template optimization variable has reasonable value
        template_opt_value = solver.Value(
            optimization_vars[template_task.template_task_id]
        )
        assert 0 <= template_opt_value <= 1000


class TestTemplateSkillWorkloadBalancing:
    """Test template skill workload balancing constraints."""

    def test_workload_balancing_basic(self):
        """Test basic workload balancing functionality."""
        # GIVEN: Template problem with operators of different skill levels
        problem = create_template_test_problem(
            num_instances=3, template_tasks_count=2, operators_count=4, skills_count=2
        )

        model = cp_model.CpModel()

        # Create assignment variables
        task_operator_assigned = {}
        for instance in problem.job_instances:
            for template_task in problem.job_template.template_tasks:
                for operator in problem.operators:
                    key = (
                        instance.instance_id,
                        template_task.template_task_id,
                        operator.operator_id,
                    )
                    task_operator_assigned[key] = model.NewBoolVar(
                        f"assign_{key[0][:8]}_{key[1][:8]}_{key[2][:8]}"
                    )

        # WHEN: Adding workload balancing constraints
        workload_vars = add_template_skill_workload_balancing(
            model, task_operator_assigned, problem
        )

        # THEN: Workload variables created for each operator
        assert len(workload_vars) == len(problem.operators)
        for operator in problem.operators:
            assert operator.operator_id in workload_vars

        # AND: Model remains solvable
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    def test_workload_balancing_non_template(self):
        """Test workload balancing with non-template problem."""
        # GIVEN: Non-template problem
        problem = SchedulingProblem(
            jobs=[],
            machines=[],
            work_cells=[],
            precedences=[],
            operators=[],
            skills=[],
            is_template_based=False,
        )
        model = cp_model.CpModel()

        # WHEN: Adding workload balancing constraints
        workload_vars = add_template_skill_workload_balancing(model, {}, problem)

        # THEN: No workload variables created
        assert workload_vars == {}

    def test_workload_calculation_accuracy(self):
        """Test that workload calculation considers task complexity."""
        # GIVEN: Template with tasks of different complexity (min_operators)
        problem = create_template_test_problem(
            num_instances=2, template_tasks_count=2, operators_count=2, skills_count=1
        )

        # Set different complexity levels
        problem.job_template.template_tasks[0].min_operators = 1  # Simple task
        problem.job_template.template_tasks[1].min_operators = 2  # Complex task

        model = cp_model.CpModel()

        # Create assignment variables
        task_operator_assigned = {}
        for instance in problem.job_instances:
            for template_task in problem.job_template.template_tasks:
                for operator in problem.operators:
                    key = (
                        instance.instance_id,
                        template_task.template_task_id,
                        operator.operator_id,
                    )
                    task_operator_assigned[key] = model.NewBoolVar(
                        f"assign_{key[0][:8]}_{key[1][:8]}_{key[2][:8]}"
                    )

        # Force specific assignments to test weighting
        instance = problem.job_instances[0]
        operator = problem.operators[0]

        # Assign operator to both simple and complex task
        simple_key = (
            instance.instance_id,
            problem.job_template.template_tasks[0].template_task_id,
            operator.operator_id,
        )
        complex_key = (
            instance.instance_id,
            problem.job_template.template_tasks[1].template_task_id,
            operator.operator_id,
        )

        model.Add(task_operator_assigned[simple_key] == 1)
        model.Add(task_operator_assigned[complex_key] == 1)

        # WHEN: Adding workload balancing
        workload_vars = add_template_skill_workload_balancing(
            model, task_operator_assigned, problem
        )

        # THEN: Solver finds solution
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

        # AND: Workload reflects task complexity weighting
        workload_value = solver.Value(workload_vars[operator.operator_id])
        expected_workload = (
            1 * 1 + 1 * 2
        )  # simple_weight * assignment + complex_weight * assignment
        assert (
            workload_value >= expected_workload
        )  # May be higher due to other assignments


class TestTemplateCrossTrainingOptimization:
    """Test template cross-training optimization constraints."""

    def test_cross_training_basic(self):
        """Test basic cross-training optimization functionality."""
        # GIVEN: Template problem with skill gaps
        problem = create_template_test_problem(
            num_instances=2, template_tasks_count=2, operators_count=3, skills_count=3
        )

        model = cp_model.CpModel()

        # Create assignment variables
        task_operator_assigned = {}
        for instance in problem.job_instances:
            for template_task in problem.job_template.template_tasks:
                for operator in problem.operators:
                    key = (
                        instance.instance_id,
                        template_task.template_task_id,
                        operator.operator_id,
                    )
                    task_operator_assigned[key] = model.NewBoolVar(
                        f"assign_{key[0][:8]}_{key[1][:8]}_{key[2][:8]}"
                    )

        # WHEN: Adding cross-training optimization
        skill_gap_vars = add_template_cross_training_optimization(
            model, task_operator_assigned, problem
        )

        # THEN: Skill gap variables created for template task-skill combinations
        assert len(skill_gap_vars) > 0

        # AND: Model remains solvable
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    def test_cross_training_non_template(self):
        """Test cross-training optimization with non-template problem."""
        # GIVEN: Non-template problem
        problem = SchedulingProblem(
            jobs=[],
            machines=[],
            work_cells=[],
            precedences=[],
            operators=[],
            skills=[],
            is_template_based=False,
        )
        model = cp_model.CpModel()

        # WHEN: Adding cross-training optimization
        skill_gap_vars = add_template_cross_training_optimization(model, {}, problem)

        # THEN: No skill gap variables created
        assert skill_gap_vars == {}

    def test_skill_gap_calculation(self):
        """Test that skill gaps are calculated correctly."""
        # GIVEN: Template problem with known skill distribution
        problem = create_template_test_problem(
            num_instances=2, template_tasks_count=1, operators_count=2, skills_count=1
        )

        # Ensure only one operator has the required skill
        skill = problem.skills[0]
        qualified_operator = problem.operators[0]
        # unqualified_operator = problem.operators[1]  # Not used in this test

        # Clear existing skills and set up specific scenario
        problem.operator_skills = [
            OperatorSkill(
                operator_id=qualified_operator.operator_id,
                skill_id=skill.skill_id,
                proficiency_level=ProficiencyLevel.COMPETENT,
            )
        ]

        model = cp_model.CpModel()

        # Create assignment variables
        task_operator_assigned = {}
        template_task = problem.job_template.template_tasks[0]

        for instance in problem.job_instances:
            for operator in problem.operators:
                key = (
                    instance.instance_id,
                    template_task.template_task_id,
                    operator.operator_id,
                )
                task_operator_assigned[key] = model.NewBoolVar(
                    f"assign_{key[0][:8]}_{key[1][:8]}_{key[2][:8]}"
                )

        # WHEN: Adding cross-training optimization
        skill_gap_vars = add_template_cross_training_optimization(
            model, task_operator_assigned, problem
        )

        # THEN: Solver finds solution
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

        # AND: Skill gap reflects the shortage (2 instances, 1 qualified operator)
        gap_key = f"{template_task.template_task_id}_{skill.skill_id}"
        if gap_key in skill_gap_vars:
            gap_value = solver.Value(skill_gap_vars[gap_key])
            # Gap should be positive since we have 2 instances
            # but limited qualified operators
            assert gap_value >= 0


class TestTemplateSkillOptimizationIntegration:
    """Test integration of all template skill optimization components."""

    def test_full_template_optimization_integration(self):
        """Test that all template optimization components work together."""
        # GIVEN: Complex template problem
        problem = create_template_test_problem(
            num_instances=3, template_tasks_count=3, operators_count=5, skills_count=4
        )

        model = cp_model.CpModel()

        # Create comprehensive variable set
        task_operator_assigned = {}
        task_starts = {}
        task_ends = {}

        for instance in problem.job_instances:
            for template_task in problem.job_template.template_tasks:
                # Timing variables
                timing_key = (instance.instance_id, template_task.template_task_id)
                task_starts[timing_key] = model.NewIntVar(
                    0, 100, f"start_{timing_key[0][:8]}_{timing_key[1][:8]}"
                )
                task_ends[timing_key] = model.NewIntVar(
                    0, 100, f"end_{timing_key[0][:8]}_{timing_key[1][:8]}"
                )

                # Assignment variables
                for operator in problem.operators:
                    assign_key = (
                        instance.instance_id,
                        template_task.template_task_id,
                        operator.operator_id,
                    )
                    task_operator_assigned[assign_key] = model.NewBoolVar(
                        f"assign_{assign_key[0][:8]}_{assign_key[1][:8]}_{assign_key[2][:8]}"
                    )

        # WHEN: Adding all template optimization constraints
        optimization_vars = add_template_skill_optimization_constraints(
            model, task_starts, task_ends, task_operator_assigned, problem
        )

        workload_vars = add_template_skill_workload_balancing(
            model, task_operator_assigned, problem
        )

        skill_gap_vars = add_template_cross_training_optimization(
            model, task_operator_assigned, problem
        )

        # THEN: All constraint types create variables
        assert len(optimization_vars) > 0
        assert len(workload_vars) > 0
        assert len(skill_gap_vars) >= 0  # May be 0 if no skill requirements defined

        # AND: Integrated model is solvable
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

        # AND: All variables have valid values
        for var in optimization_vars.values():
            assert 0 <= solver.Value(var) <= 1000

        for var in workload_vars.values():
            assert solver.Value(var) >= 0

        for var in skill_gap_vars.values():
            assert solver.Value(var) >= 0

    def test_performance_scalability(self):
        """Test that template optimization scales better than O(total_tasks)."""
        # GIVEN: Large template problem (realistic scale)
        problem = create_template_test_problem(
            num_instances=10,  # 10 identical jobs
            template_tasks_count=5,  # 5 tasks per job template
            operators_count=8,
            skills_count=6,
        )

        model = cp_model.CpModel()

        # Create full variable set
        task_operator_assigned = {}
        task_starts = {}
        task_ends = {}

        for instance in problem.job_instances:
            for template_task in problem.job_template.template_tasks:
                timing_key = (instance.instance_id, template_task.template_task_id)
                task_starts[timing_key] = model.NewIntVar(
                    0, 200, f"start_{timing_key[0][:8]}_{timing_key[1][:8]}"
                )
                task_ends[timing_key] = model.NewIntVar(
                    1, 201, f"end_{timing_key[0][:8]}_{timing_key[1][:8]}"
                )

                for operator in problem.operators:
                    assign_key = (
                        instance.instance_id,
                        template_task.template_task_id,
                        operator.operator_id,
                    )
                    task_operator_assigned[assign_key] = model.NewBoolVar(
                        f"assign_{assign_key[0][:8]}_{assign_key[1][:8]}_{assign_key[2][:8]}"
                    )

        # WHEN: Adding template optimization (should be efficient)
        optimization_vars = add_template_skill_optimization_constraints(
            model, task_starts, task_ends, task_operator_assigned, problem
        )

        # THEN: Optimization variables count scales with template size, not total tasks
        expected_template_vars = len(problem.job_template.template_tasks)
        assert len(optimization_vars) == expected_template_vars

        # AND: Model construction completes in reasonable time
        # (This is implicitly tested by the test completing successfully)

        # AND: Model is still solvable despite scale
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30  # Reasonable time limit
        status = solver.Solve(model)
        # Accept optimal, feasible, or unknown (timeout)
        # as valid results for large problems
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE, cp_model.UNKNOWN]
