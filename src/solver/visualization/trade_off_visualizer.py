"""Simple text-based visualization utilities for trade-off analysis.

Provides terminal-friendly visualizations to help users understand
multi-objective optimization results and trade-offs between strategies.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.solver.models.problem import (
    ObjectiveType,
    ParetoFrontier,
    ParetoSolution,
)

logger = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    """Container for optimization strategy results."""

    name: str
    total_lateness: float
    makespan: float
    total_cost: float
    solve_time: float
    strategy_type: str


def create_strategy_comparison_table(results: dict[str, Any]) -> str:
    """Create a formatted comparison table for different optimization strategies.

    Args:
        results: Dictionary containing results from different strategies
                (lexicographic, weighted_sum, pareto, etc.)

    Returns:
        Formatted string table comparing strategies

    """
    logger.info("Creating strategy comparison table...")

    strategies = _extract_strategy_results(results)

    if not strategies:
        return "No valid strategy results found for comparison."

    # Create table header
    table_lines = []
    table_lines.append("=" * 85)
    table_lines.append("MULTI-OBJECTIVE OPTIMIZATION STRATEGY COMPARISON")
    table_lines.append("=" * 85)
    table_lines.append("")

    # Table column headers
    header = (
        f"{'Strategy':20} | {'Lateness':>9} | {'Makespan':>9} | "
        f"{'Cost':>12} | {'Time (s)':>8} | {'Type':12}"
    )
    table_lines.append(header)
    table_lines.append("-" * 85)

    # Add strategy rows
    for strategy in strategies:
        cost_str = (
            f"${strategy.total_cost:,.2f}"
            if strategy.total_cost is not None
            else "$0.00"
        )
        time_str = (
            f"{strategy.solve_time:.2f}" if strategy.solve_time is not None else "N/A"
        )

        row = (
            f"{strategy.name:20} | "
            f"{strategy.total_lateness:>9.0f} | "
            f"{strategy.makespan:>9.0f} | "
            f"{cost_str:>12} | "
            f"{time_str:>8} | "
            f"{strategy.strategy_type:12}"
        )
        table_lines.append(row)

    table_lines.append("-" * 85)

    # Add insights
    table_lines.append("")
    table_lines.append("KEY INSIGHTS:")
    table_lines.append("")

    # Find best performer for each objective
    best_lateness = min(
        strategies,
        key=lambda x: (
            x.total_lateness if x.total_lateness is not None else float("inf")
        ),
    )
    best_makespan = min(
        strategies, key=lambda x: x.makespan if x.makespan is not None else float("inf")
    )
    best_cost = min(
        strategies,
        key=lambda x: x.total_cost if x.total_cost is not None else float("inf"),
    )
    fastest_solve = min(
        strategies,
        key=lambda x: x.solve_time if x.solve_time is not None else float("inf"),
    )

    table_lines.append(
        f"• Best Lateness:  {best_lateness.name} ({best_lateness.total_lateness:.0f})"
    )
    table_lines.append(
        f"• Best Makespan:  {best_makespan.name} ({best_makespan.makespan:.0f})"
    )
    table_lines.append(
        f"• Best Cost:      {best_cost.name} (${best_cost.total_cost:,.2f})"
    )
    table_lines.append(
        f"• Fastest Solve:  {fastest_solve.name} ({fastest_solve.solve_time:.2f}s)"
    )

    # Add strategy-specific insights
    table_lines.append("")
    table_lines.append("STRATEGY ANALYSIS:")
    for strategy in strategies:
        if "lexicographic" in strategy.name.lower():
            table_lines.append(
                f"• {strategy.name}: Prioritizes objectives in order - "
                f"guarantees optimal lateness first"
            )
        elif "weighted" in strategy.name.lower():
            table_lines.append(
                f"• {strategy.name}: Balances all objectives simultaneously "
                f"based on weights"
            )
        elif "pareto" in strategy.name.lower():
            table_lines.append(
                f"• {strategy.name}: Finds balanced trade-off solution "
                f"from Pareto frontier"
            )

    table_lines.append("")
    table_lines.append("=" * 85)

    return "\n".join(table_lines)


def create_objective_bar_chart(results: dict[str, Any], objective: str = "all") -> str:
    """Create simple ASCII bar charts for objective comparisons.

    Args:
        results: Dictionary containing results from different strategies
        objective: Which objective to chart ("lateness", "makespan", "cost", or "all")

    Returns:
        Formatted string with ASCII bar charts

    """
    logger.info(f"Creating objective bar chart for: {objective}")

    strategies = _extract_strategy_results(results)

    if not strategies:
        return "No valid strategy results found for bar chart."

    chart_lines = []
    chart_lines.append("=" * 70)
    chart_lines.append("OBJECTIVE PERFORMANCE COMPARISON")
    chart_lines.append("=" * 70)
    chart_lines.append("")

    if objective == "all" or objective == "lateness":
        chart_lines.extend(
            _create_single_objective_chart(
                strategies, "Total Lateness", lambda s: s.total_lateness, "units"
            )
        )
        chart_lines.append("")

    if objective == "all" or objective == "makespan":
        chart_lines.extend(
            _create_single_objective_chart(
                strategies, "Makespan", lambda s: s.makespan, "time units"
            )
        )
        chart_lines.append("")

    if objective == "all" or objective == "cost":
        chart_lines.extend(
            _create_single_objective_chart(
                strategies,
                "Total Cost",
                lambda s: s.total_cost,
                "dollars",
                is_currency=True,
            )
        )
        chart_lines.append("")

    chart_lines.append("=" * 70)

    return "\n".join(chart_lines)


def create_pareto_frontier_plot(
    frontier: ParetoFrontier, max_solutions: int = 10
) -> str:
    """Create a simple text-based plot of the Pareto frontier.

    Args:
        frontier: ParetoFrontier containing solutions
        max_solutions: Maximum number of solutions to display

    Returns:
        Formatted string showing Pareto frontier solutions

    """
    logger.info("Creating Pareto frontier plot...")

    if frontier.solution_count == 0:
        return "No Pareto solutions found."

    plot_lines = []
    plot_lines.append("=" * 80)
    plot_lines.append("PARETO FRONTIER SOLUTIONS")
    plot_lines.append("=" * 80)
    plot_lines.append("")

    # Show solution count
    total_solutions = frontier.solution_count
    showing = min(max_solutions, total_solutions)
    plot_lines.append(
        f"Showing {showing} of {total_solutions} Pareto-optimal solutions:"
    )
    plot_lines.append("")

    # Create header for solutions table
    header = (
        f"{'Solution':>8} | {'Lateness':>9} | {'Makespan':>9} | "
        f"{'Cost':>12} | {'Trade-off Profile':20}"
    )
    plot_lines.append(header)
    plot_lines.append("-" * 80)

    # Show solutions
    solutions = frontier.solutions[:max_solutions]
    for i, solution in enumerate(solutions, 1):
        lateness = (
            solution.objectives.get_objective_value(
                ObjectiveType.MINIMIZE_TOTAL_LATENESS
            )
            or 0
        )
        makespan = (
            solution.objectives.get_objective_value(ObjectiveType.MINIMIZE_MAKESPAN)
            or 0
        )
        cost = (
            solution.objectives.get_objective_value(ObjectiveType.MINIMIZE_TOTAL_COST)
            or 0
        )

        cost_str = f"${cost:,.2f}" if cost is not None else "$0.00"

        # Create simple trade-off profile
        profile = _generate_trade_off_profile(lateness, makespan, cost, solutions)

        row = (
            f"#{i:>7} | "
            f"{lateness:>9.0f} | "
            f"{makespan:>9.0f} | "
            f"{cost_str:>12} | "
            f"{profile:20}"
        )
        plot_lines.append(row)

    plot_lines.append("-" * 80)

    if total_solutions > max_solutions:
        plot_lines.append(f"... and {total_solutions - max_solutions} more solutions")
        plot_lines.append("")

    # Add frontier analysis
    plot_lines.append("")
    plot_lines.append("FRONTIER ANALYSIS:")
    plot_lines.append("")

    # Calculate ranges
    lateness_values = [
        s.objectives.get_objective_value(ObjectiveType.MINIMIZE_TOTAL_LATENESS) or 0
        for s in frontier.solutions
    ]
    makespan_values = [
        s.objectives.get_objective_value(ObjectiveType.MINIMIZE_MAKESPAN) or 0
        for s in frontier.solutions
    ]
    cost_values = [
        s.objectives.get_objective_value(ObjectiveType.MINIMIZE_TOTAL_COST) or 0
        for s in frontier.solutions
    ]

    if lateness_values:
        plot_lines.append(
            f"• Lateness range: {min(lateness_values):.0f} - {max(lateness_values):.0f}"
        )
    if makespan_values:
        plot_lines.append(
            f"• Makespan range: {min(makespan_values):.0f} - {max(makespan_values):.0f}"
        )
    if cost_values:
        plot_lines.append(
            f"• Cost range: ${min(cost_values):,.2f} - ${max(cost_values):,.2f}"
        )

    plot_lines.append("")
    plot_lines.append("=" * 80)

    return "\n".join(plot_lines)


def visualize_optimization_results(
    results: dict[str, Any], include_pareto: bool = True, include_charts: bool = True
) -> str:
    """Create comprehensive visualization of optimization results.

    Args:
        results: Dictionary containing results from different strategies
        include_pareto: Whether to include Pareto frontier visualization
        include_charts: Whether to include objective bar charts

    Returns:
        Complete formatted visualization report

    """
    logger.info("Creating comprehensive optimization results visualization...")

    report_lines = []

    # Main comparison table
    report_lines.append(create_strategy_comparison_table(results))
    report_lines.append("")

    # Objective bar charts
    if include_charts:
        report_lines.append(create_objective_bar_chart(results))
        report_lines.append("")

    # Pareto frontier plot
    if include_pareto and "pareto" in results:
        pareto_result = results.get("pareto", {})
        if "pareto_frontier" in pareto_result:
            frontier = pareto_result["pareto_frontier"]
            if hasattr(frontier, "solution_count") and frontier.solution_count > 0:
                report_lines.append(create_pareto_frontier_plot(frontier))
                report_lines.append("")

    # Summary recommendations
    report_lines.append(_create_recommendations_summary(results))

    return "\n".join(report_lines)


# Helper functions


def _extract_strategy_results(results: dict[str, Any]) -> list[StrategyResult]:
    """Extract StrategyResult objects from raw results dictionary."""
    strategies = []

    # Extract lexicographic results
    if "lexicographic" in results:
        lex_result = results["lexicographic"]
        if "multi_objective" in lex_result:
            multi_obj = lex_result["multi_objective"]
            strategies.append(
                StrategyResult(
                    name="Lexicographic",
                    total_lateness=multi_obj.get("total_lateness", 0),
                    makespan=multi_obj.get("makespan", 0),
                    total_cost=multi_obj.get("total_cost", 0),
                    solve_time=lex_result.get("solve_time", 0),
                    strategy_type="Sequential",
                )
            )

    # Extract weighted sum results
    if "weighted_sum" in results:
        ws_result = results["weighted_sum"]
        if "multi_objective" in ws_result:
            multi_obj = ws_result["multi_objective"]
            strategies.append(
                StrategyResult(
                    name="Weighted Sum",
                    total_lateness=multi_obj.get("total_lateness", 0),
                    makespan=multi_obj.get("makespan", 0),
                    total_cost=multi_obj.get("total_cost", 0),
                    solve_time=ws_result.get("solve_time", 0),
                    strategy_type="Simultaneous",
                )
            )

    # Extract Pareto results (recommended solution)
    if "pareto" in results:
        pareto_result = results["pareto"]
        if "recommended_solution" in pareto_result:
            rec_obj = pareto_result["recommended_solution"]["objectives"]
            # Handle different objective extraction methods
            if hasattr(rec_obj, "get_objective_value"):
                total_lateness = (
                    rec_obj.get_objective_value(ObjectiveType.MINIMIZE_TOTAL_LATENESS)
                    or 0
                )
                makespan = (
                    rec_obj.get_objective_value(ObjectiveType.MINIMIZE_MAKESPAN) or 0
                )
                total_cost = (
                    rec_obj.get_objective_value(ObjectiveType.MINIMIZE_TOTAL_COST) or 0
                )
            else:
                # Handle mock object or dictionary-like access
                total_lateness = getattr(rec_obj, "total_lateness", 0)
                makespan = getattr(rec_obj, "makespan", 0)
                total_cost = getattr(rec_obj, "total_cost", 0)

            strategies.append(
                StrategyResult(
                    name="Pareto (Recommended)",
                    total_lateness=total_lateness,
                    makespan=makespan,
                    total_cost=total_cost,
                    solve_time=pareto_result.get("solve_time", 0),
                    strategy_type="Multi-solution",
                )
            )

    return strategies


def _create_single_objective_chart(
    strategies: list[StrategyResult],
    title: str,
    value_func: Callable[[StrategyResult], float],
    units: str,
    is_currency: bool = False,
) -> list[str]:
    """Create ASCII bar chart for a single objective."""
    chart_lines = []
    chart_lines.append(f"{title.upper()} COMPARISON:")
    chart_lines.append("")

    # Get values and find max for scaling
    values = [(s.name, value_func(s) or 0) for s in strategies]
    max_value = max(v[1] for v in values) if values else 1

    # Create bars (scale to 50 characters max)
    max_bar_length = 50

    for name, value in values:
        bar_length = int(value / max_value * max_bar_length) if max_value > 0 else 0

        bar = "█" * bar_length + "░" * (max_bar_length - bar_length)

        value_str = f"${value:,.2f}" if is_currency else f"{value:,.1f} {units}"

        chart_lines.append(f"{name:20} |{bar}| {value_str}")

    return chart_lines


def _generate_trade_off_profile(
    lateness: float, makespan: float, cost: float, _all_solutions: list[ParetoSolution]
) -> str:
    """Generate a simple trade-off profile string for a solution."""
    # Create simple categorization based on relative performance
    if lateness == 0:
        lateness_profile = "No-Late"
    elif lateness < 10:
        lateness_profile = "Low-Late"
    else:
        lateness_profile = "High-Late"

    if makespan < 20:
        makespan_profile = "Fast"
    elif makespan < 40:
        makespan_profile = "Medium"
    else:
        makespan_profile = "Slow"

    if cost < 200:
        cost_profile = "Cheap"
    elif cost < 400:
        cost_profile = "Medium"
    else:
        cost_profile = "Expensive"

    return f"{lateness_profile}/{makespan_profile}/{cost_profile}"


def _create_recommendations_summary(results: dict[str, Any]) -> str:
    """Create a summary with recommendations based on the results."""
    summary_lines = []
    summary_lines.append("=" * 80)
    summary_lines.append("RECOMMENDATIONS & INSIGHTS")
    summary_lines.append("=" * 80)
    summary_lines.append("")

    strategies = _extract_strategy_results(results)

    if not strategies:
        summary_lines.append("No strategy results available for recommendations.")
        return "\n".join(summary_lines)

    # Find best strategies for different scenarios
    best_overall_lateness = min(
        strategies,
        key=lambda x: (
            x.total_lateness if x.total_lateness is not None else float("inf")
        ),
    )
    best_balanced = min(
        strategies,
        key=lambda x: (x.total_lateness if x.total_lateness is not None else 0)
        + (x.makespan if x.makespan is not None else 0)
        + (x.total_cost if x.total_cost is not None else 0) / 10,
    )
    fastest_solver = min(
        strategies,
        key=lambda x: x.solve_time if x.solve_time is not None else float("inf"),
    )

    summary_lines.append("STRATEGY RECOMMENDATIONS:")
    summary_lines.append("")

    summary_lines.append(f"• For CRITICAL DEADLINES: Use {best_overall_lateness.name}")
    summary_lines.append(
        f"  - Minimizes lateness: {best_overall_lateness.total_lateness:.0f}"
    )
    summary_lines.append("  - Best when on-time delivery is paramount")
    summary_lines.append("")

    summary_lines.append(f"• For BALANCED OPTIMIZATION: Use {best_balanced.name}")
    summary_lines.append("  - Good trade-off across all objectives")
    summary_lines.append("  - Suitable for most production scenarios")
    summary_lines.append("")

    summary_lines.append(f"• For FAST DECISIONS: Use {fastest_solver.name}")
    summary_lines.append(f"  - Solves in {fastest_solver.solve_time:.2f} seconds")
    summary_lines.append("  - Good for real-time or interactive planning")
    summary_lines.append("")

    # Add general insights
    summary_lines.append("GENERAL INSIGHTS:")
    summary_lines.append("")

    if any("lexicographic" in s.name.lower() for s in strategies):
        summary_lines.append(
            "• Lexicographic optimization provides guaranteed priority ordering"
        )
        summary_lines.append("  - Use when objectives have clear priority hierarchy")
        summary_lines.append(
            "  - Ensures higher priority objectives are never compromised"
        )
        summary_lines.append("")

    if any("weighted" in s.name.lower() for s in strategies):
        summary_lines.append(
            "• Weighted sum optimization balances all objectives simultaneously"
        )
        summary_lines.append("  - Use when all objectives are equally important")
        summary_lines.append(
            "  - Faster solving but may not guarantee priority ordering"
        )
        summary_lines.append("")

    if any("pareto" in s.name.lower() for s in strategies):
        summary_lines.append(
            "• Pareto optimization explores multiple trade-off solutions"
        )
        summary_lines.append("  - Use when you want to see all possible trade-offs")
        summary_lines.append("  - Helps with scenario analysis and decision making")
        summary_lines.append("")

    summary_lines.append("=" * 80)

    return "\n".join(summary_lines)
