#!/usr/bin/env python3
"""Production Integration Demo for OR-Tools Template-Based Solver.

This script demonstrates the complete integration of all three enhancement systems:
1. Template Parameter Management System
2. Performance Infrastructure
3. Production Monitoring

It showcases the 5-8x performance improvements achieved through template-based
optimization with comprehensive monitoring and alerting.
"""

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run production integration demonstration."""
    print("🚀 OR-Tools Template-Based Solver - Production Integration Demo")
    print("=" * 80)

    try:
        # 1. Template Parameter Management System Demo
        print("\n📊 1. Template Parameter Management System")
        print("-" * 50)
        demo_parameter_management()

        # 2. Performance Infrastructure Demo
        print("\n⚡ 2. Performance Infrastructure")
        print("-" * 50)
        demo_performance_infrastructure()

        # 3. Production Monitoring Demo
        print("\n🔍 3. Production Monitoring")
        print("-" * 50)
        demo_production_monitoring()

        # 4. Integrated System Demo
        print("\n🔄 4. Integrated System Workflow")
        print("-" * 50)
        demo_integrated_workflow()

        print("\n✅ Production Integration Demo Complete!")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")


def demo_parameter_management():
    """Demonstrate Template Parameter Management System."""
    try:
        import sys
        from pathlib import Path

        # Add src to path for imports
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

        from solver.templates import (
            OptimizedOptimizer,
            OptimizedValidator,
            ParameterManager,
        )

        print("✅ Template management modules loaded successfully")

        # Initialize parameter manager
        param_manager = ParameterManager()
        print(f"📁 Parameter storage: {param_manager.storage_path}")

        # Demonstrate parameter validation
        test_params = {
            "num_search_workers": 8,
            "max_time_in_seconds": 60,
            "linearization_level": 1,
            "search_branching": "FIXED_SEARCH",
        }

        validation_result = param_manager.validate_parameters(
            "demo_template", test_params
        )

        status = "✅ Valid" if validation_result.is_valid else "❌ Invalid"
        print(f"📝 Parameter validation: {status}")
        print(f"🚀 Expected speedup: {validation_result.speedup_factor:.1f}x")

        # Show blessed parameters count
        blessed_count = len(param_manager.list_blessed_parameters())
        print(f"🏆 Blessed parameters available: {blessed_count}")

        # Initialize optimizer and validator
        OptimizedOptimizer()  # noqa: F841
        OptimizedValidator()  # noqa: F841

        print("✅ Template optimizer and validator ready")

    except ImportError as e:
        print(f"❌ Template system not available: {e}")
    except Exception as e:
        print(f"❌ Parameter management demo failed: {e}")


def demo_performance_infrastructure():
    """Demonstrate Performance Infrastructure."""
    try:
        import sys
        from pathlib import Path

        # Add src to path for imports
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

        from performance import (
            BenchmarkRunner,
            RegressionDetector,
            TemplateBenchmark,
        )

        print("✅ Performance infrastructure modules loaded successfully")

        # Initialize benchmark runner
        benchmark_runner = BenchmarkRunner()
        print(f"📊 Benchmark results storage: {benchmark_runner.results_dir}")

        # Create benchmark configuration
        benchmark_config = TemplateBenchmark(
            template_id="demo_manufacturing_v1",
            instance_counts=[1, 3, 5],
            time_limit_seconds=30,
            repetitions=2,
        )

        print(f"⚙️  Benchmark config: {benchmark_config.template_id}")
        print(f"📈 Testing instance counts: {benchmark_config.instance_counts}")

        # Run benchmark (simulated)
        benchmark_suite = benchmark_runner.run_template_benchmark(benchmark_config)

        result_count = len(benchmark_suite.results)
        print(f"🎯 Benchmark results: {result_count} instance counts tested")
        print(f"🚀 Average speedup: {benchmark_suite.average_speedup:.1f}x")
        print(f"📊 Scalability factor: {benchmark_suite.scalability_factor:.2f}")

        # Initialize regression detector
        RegressionDetector()  # noqa: F841
        print("✅ Regression detection system ready")

        # Show performance trends
        trends = benchmark_runner.get_performance_trends("demo_manufacturing_v1")
        print(f"📈 Performance trend analysis: {trends.get('speedup_trend', 'stable')}")

    except ImportError as e:
        print(f"❌ Performance infrastructure not available: {e}")
    except Exception as e:
        print(f"❌ Performance infrastructure demo failed: {e}")


def demo_production_monitoring():
    """Demonstrate Production Monitoring."""
    try:
        import sys
        from pathlib import Path

        # Add src to path for imports
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

        from operations import AlertManager, HealthChecker, PerformanceMonitor

        print("✅ Production monitoring modules loaded successfully")

        # Initialize performance monitor
        perf_monitor = PerformanceMonitor()

        # Record sample performance data
        perf_monitor.record_solve_performance(
            template_id="demo_template",
            solve_time=2.5,
            instance_count=5,
            solver_status="OPTIMAL",
            memory_usage_mb=150,
        )

        perf_monitor.record_system_metrics(
            cpu_percent=45.2, memory_percent=62.1, disk_usage_percent=35.8
        )

        print(f"📊 Performance metrics recorded: {len(perf_monitor.metrics)}")

        # Get current health status
        health_metrics = perf_monitor.get_current_health()
        health_score = health_metrics.overall_health_score
        health_status = health_metrics.status.value
        print(f"💚 System health: {health_status} (score: {health_score:.1f})")
        print(f"🔧 Active templates: {health_metrics.active_templates}")

        # Initialize health checker
        health_checker = HealthChecker()

        # Run health checks
        health_results = health_checker.run_all_checks()
        passed = sum(1 for r in health_results if r.is_healthy)
        print(f"🏥 Health checks: {passed}/{len(health_results)} passed")

        # Initialize alert manager
        alert_manager = AlertManager()

        # Create sample alert
        alert = alert_manager.create_performance_alert(
            template_id="demo_template",
            current_time=8.2,
            baseline_time=3.1,
            threshold_percent=50.0,
        )

        if alert:
            print(f"🚨 Performance alert created: {alert.title}")

        # Show alert statistics
        alert_stats = alert_manager.get_alert_statistics()
        total_alerts = alert_stats["total_alerts"]
        active_alerts = alert_stats["active_alerts"]
        print(f"📈 Alert statistics: {total_alerts} total, {active_alerts} active")

    except ImportError as e:
        print(f"❌ Production monitoring not available: {e}")
    except Exception as e:
        print(f"❌ Production monitoring demo failed: {e}")


def demo_integrated_workflow():
    """Demonstrate integrated workflow across all systems."""
    try:
        import sys
        from pathlib import Path

        # Add src to path for imports
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

        from operations import AlertManager, PerformanceMonitor
        from performance import BenchmarkRunner, TemplateBenchmark
        from solver.templates import ParameterManager

        print("🔄 Integrated Production Workflow Demo")

        # 1. Parameter Management
        param_manager = ParameterManager()
        template_id = "integrated_demo_v1"

        # Get blessed parameters (or defaults)
        solver_params = param_manager.get_solver_parameters(template_id)
        print(f"⚙️  Solver parameters: {len(solver_params)} parameters loaded")

        # 2. Performance Benchmarking
        benchmark_runner = BenchmarkRunner()
        benchmark_config = TemplateBenchmark(
            template_id=template_id,
            instance_counts=[3, 5],
            time_limit_seconds=15,
            parameters=solver_params,
        )

        # Run benchmark with blessed parameters
        benchmark_suite = benchmark_runner.run_template_benchmark(benchmark_config)
        speedup = benchmark_suite.average_speedup
        print(f"📊 Benchmark with blessed parameters: {speedup:.1f}x speedup")

        # 3. Performance Monitoring
        perf_monitor = PerformanceMonitor()
        alert_manager = AlertManager()

        # Record performance from benchmark
        for result in benchmark_suite.successful_results:
            perf_monitor.record_solve_performance(
                template_id=result.template_id,
                solve_time=result.solve_time,
                instance_count=result.instance_count,
                solver_status=result.solver_status,
                memory_usage_mb=result.memory_usage_mb,
            )

        solves_count = len(benchmark_suite.successful_results)
        print(f"📈 Performance data recorded: {solves_count} solves")

        # 4. Health and Alerting
        health_metrics = perf_monitor.get_current_health()

        # Simulate performance degradation alert
        # Expected 5-8x, anything under 3x is concerning
        if benchmark_suite.average_speedup < 3.0:
            alert = alert_manager.create_performance_alert(
                template_id=template_id,
                current_time=5.0,
                baseline_time=1.5,
                threshold_percent=50.0,
            )
            if alert:
                print("⚠️  Performance degradation detected and alerted")

        # 5. Integrated Summary
        print("\n📋 Integrated System Summary:")
        print(f"   🏆 Template: {template_id}")
        print(f"   ⚙️  Parameters: {len(solver_params)} optimized settings")
        performance_speedup = benchmark_suite.average_speedup
        print(f"   🚀 Performance: {performance_speedup:.1f}x speedup achieved")
        print(f"   💚 Health: {health_metrics.status.value}")
        print(f"   🚨 Alerts: {len(alert_manager.active_alerts)} active")

        print("✅ Integrated workflow demonstrates all systems working together!")

    except Exception as e:
        print(f"❌ Integrated workflow demo failed: {e}")


if __name__ == "__main__":
    main()
