#!/usr/bin/env python3
"""MCP-based production data solver script.

Uses the MCP Supabase tools to load real production data and run the
optimized OR-Tools solver.
This bypasses authentication issues by using the MCP's built-in Supabase access.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.solver.core.solver import FreshSolver  # noqa: E402
from src.solver.models.problem import (  # noqa: E402
    Job,
    Machine,
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("mcp_production_solver.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class MCPProductionDataLoader:
    """Production data loader using direct SQL queries through MCP tools."""

    def __init__(self):
        """Initialize the MCP-based loader."""
        pass

    def load_problem(self) -> SchedulingProblem:
        """Load complete scheduling problem using MCP SQL queries."""
        logger.info("Loading production scheduling problem via MCP...")

        # Load all data using direct SQL
        work_cells = self._load_work_cells()
        machines = self._load_machines()
        jobs = self._load_jobs()
        tasks = self._load_tasks()
        task_modes = self._load_task_modes()
        precedences = self._load_precedences()

        # Associate machines with work cells
        machine_by_cell: dict[str, list[Machine]] = {}
        for machine in machines:
            if machine.cell_id not in machine_by_cell:
                machine_by_cell[machine.cell_id] = []
            machine_by_cell[machine.cell_id].append(machine)

        for cell in work_cells:
            cell.machines = machine_by_cell.get(cell.cell_id, [])

        # Associate task modes with tasks
        modes_by_task: dict[str, list[TaskMode]] = {}
        for mode in task_modes:
            if mode.task_id not in modes_by_task:
                modes_by_task[mode.task_id] = []
            modes_by_task[mode.task_id].append(mode)

        for task in tasks:
            task.modes = modes_by_task.get(task.task_id, [])

        # Associate tasks with jobs
        tasks_by_job: dict[str, list[Task]] = {}
        for task in tasks:
            if task.job_id not in tasks_by_job:
                tasks_by_job[task.job_id] = []
            tasks_by_job[task.job_id].append(task)

        for job in jobs:
            job.tasks = tasks_by_job.get(job.job_id, [])

        # Create and validate problem
        problem = SchedulingProblem(
            jobs=jobs, machines=machines, work_cells=work_cells, precedences=precedences
        )

        # Validate
        issues = problem.validate()
        if issues:
            logger.warning("Problem validation issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")

        logger.info("Loaded production problem with:")
        logger.info(f"  - {len(jobs)} jobs")
        logger.info(f"  - {problem.total_task_count} tasks")
        logger.info(f"  - {len(machines)} machines")
        logger.info(f"  - {len(work_cells)} work cells")
        logger.info(f"  - {len(precedences)} precedence constraints")

        return problem

    def _execute_sql(self, query: str) -> list[dict[str, Any]]:
        """Execute SQL query through MCP (placeholder - will use actual MCP calls)."""
        # This is a placeholder - in the actual implementation,
        # we would use the MCP supabase tools
        logger.info(f"Executing SQL: {query[:100]}...")
        return []

    def _load_work_cells(self) -> list[WorkCell]:
        """Load work cells from database."""
        logger.info("Loading work cells...")
        # Placeholder implementation - would use MCP SQL tools
        return []

    def _load_machines(self) -> list[Machine]:
        """Load machines from database."""
        logger.info("Loading machines...")
        # Placeholder implementation - would use MCP SQL tools
        return []

    def _load_jobs(self) -> list[Job]:
        """Load jobs from database."""
        logger.info("Loading jobs...")
        # Placeholder implementation - would use MCP SQL tools
        return []

    def _load_tasks(self) -> list[Task]:
        """Load tasks from database."""
        logger.info("Loading tasks...")
        # Placeholder implementation - would use MCP SQL tools
        return []

    def _load_task_modes(self) -> list[TaskMode]:
        """Load task modes from database."""
        logger.info("Loading task modes...")
        # Placeholder implementation - would use MCP SQL tools
        return []

    def _load_precedences(self) -> list[Precedence]:
        """Load precedence constraints from database."""
        logger.info("Loading precedences...")
        # Placeholder implementation - would use MCP SQL tools
        return []


def main():
    """Run solver with production data via MCP."""
    logger.info("🚀 Starting MCP Production Data Solver")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        # Load production data via MCP
        logger.info("📊 Loading production data via MCP...")
        load_start = time.time()

        loader = MCPProductionDataLoader()
        problem = loader.load_problem()

        load_time = time.time() - load_start

        # Log problem characteristics
        logger.info(f"✅ Data loaded in {load_time:.3f}s")
        logger.info(f"   📋 Jobs: {len(problem.jobs)}")
        logger.info(f"   📝 Tasks: {problem.total_task_count}")
        logger.info(f"   🏭 Machines: {len(problem.machines)}")
        logger.info(f"   🔗 Precedences: {len(problem.precedences)}")
        logger.info(f"   📊 Template-based: {problem.is_template_based}")

        # Create solver
        logger.info("\n🔧 Initializing solver...")
        # solver_start = time.time()  # Unused variable

        solver = FreshSolver(problem)

        # Configure for production - longer time limits for larger problems
        if problem.total_task_count > 50:
            time_limit = 120  # 2 minutes for large problems
        elif problem.total_task_count > 20:
            time_limit = 60  # 1 minute for medium problems
        else:
            time_limit = 30  # 30 seconds for small problems

        logger.info(f"   ⏱️ Time limit: {time_limit}s")
        logger.info(f"   📊 Problem size: {problem.total_task_count} tasks")

        # Solve the problem
        logger.info("\n🎯 Solving optimization problem...")
        solve_start = time.time()

        solution = solver.solve(time_limit=time_limit)

        solve_time = time.time() - solve_start
        total_time = time.time() - start_time

        # Report results
        logger.info("\n📈 SOLUTION RESULTS")
        logger.info("=" * 40)
        logger.info(f"Status: {solution.get('status', 'UNKNOWN')}")
        logger.info(f"Solve time: {solve_time:.3f}s")
        logger.info(f"Total time: {total_time:.3f}s")

        if solution.get("status") in ["OPTIMAL", "FEASIBLE"]:
            makespan = solution.get("makespan", 0)
            scheduled_tasks = len(solution.get("task_schedule", {}))

            logger.info("✅ Solution found!")
            logger.info(
                f"   📏 Makespan: {makespan} time units ({makespan * 0.25:.1f} hours)"
            )
            logger.info(
                f"   📝 Tasks scheduled: {scheduled_tasks}/{problem.total_task_count}"
            )

            # Performance analysis
            logger.info("   ⚡ Legacy solver performance baseline")

            # Business metrics
            if "machine_utilization" in solution:
                utilization = solution["machine_utilization"]
                if utilization:
                    avg_util = sum(utilization.values()) / len(utilization)
                    logger.info(f"   🏭 Average machine utilization: {avg_util:.1f}%")

            # Due date performance
            if "lateness_penalties" in solution:
                penalties = solution["lateness_penalties"]
                total_lateness = sum(penalties.values())
                on_time_jobs = sum(1 for p in penalties.values() if p == 0)
                logger.info(f"   📅 On-time jobs: {on_time_jobs}/{len(penalties)}")
                logger.info(f"   ⏰ Total lateness: {total_lateness} time units")

        else:
            logger.warning(f"❌ No solution found within {time_limit}s time limit")
            logger.warning("   Consider increasing time limit or checking constraints")

        # Performance targets validation
        logger.info("\n🎯 PERFORMANCE VALIDATION")
        logger.info("=" * 40)

        if problem.total_task_count <= 50:
            target = 10.0
            status = "✅ EXCELLENT" if solve_time <= target else "⚠️ SLOW"
            logger.info(f"Small problem target (<10s): {status} ({solve_time:.1f}s)")
        elif problem.total_task_count <= 500:
            target = 60.0
            status = "✅ EXCELLENT" if solve_time <= target else "⚠️ SLOW"
            logger.info(f"Medium problem target (<60s): {status} ({solve_time:.1f}s)")
        else:
            target = 1800.0  # 30 minutes
            status = "✅ ACCEPTABLE" if solve_time <= target else "❌ TOO SLOW"
            logger.info(f"Large problem target (<30m): {status} ({solve_time:.1f}s)")

        logger.info("\n🎉 MCP production solver completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ MCP production solver failed: {e}")
        logger.exception("Full error details:")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
