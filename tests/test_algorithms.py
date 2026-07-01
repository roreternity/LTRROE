"""Sanity tests for the LTRROE scheduling core.

These check the two central claims of the model on the built-in test project:
1. CPM (deterministic critical path) produces a positive duration.
2. Monte Carlo percentiles are ordered P50 <= P90 and CPM is close to P50.
"""

import statistics

from ltrroe.core.test_data import create_test_project
from ltrroe.core.algorithms import (
    calculate_schedule,
    calculate_backward_pass,
    monte_carlo_simulation,
)


def _cpm_days(project, early_finish):
    """CPM project duration in days = latest finish minus project start."""
    return (max(early_finish.values()) - project.proj_start_date).days


def test_cpm_produces_positive_duration():
    project = create_test_project()
    early_start, early_finish, task_duration = calculate_schedule(project)
    assert early_finish, "schedule should assign finish times"
    assert _cpm_days(project, early_finish) > 0


def test_backward_pass_runs():
    project = create_test_project()
    _, early_finish, task_duration = calculate_schedule(project)
    late_start, late_finish = calculate_backward_pass(project, early_finish, task_duration)
    assert set(late_start) == set(early_finish)


def test_monte_carlo_percentiles_ordered():
    project = create_test_project()
    durations = monte_carlo_simulation(project, num_simulations=2000)
    assert len(durations) == 2000
    durations.sort()
    p50 = statistics.median(durations)
    p90 = durations[int(0.9 * len(durations)) - 1]
    assert p50 <= p90, "P50 must not exceed P90"
    assert min(durations) > 0


def test_cpm_close_to_p50():
    """CPM ~ P50: deterministic estimate should sit near the median outcome."""
    project = create_test_project()
    _, early_finish, _ = calculate_schedule(project)
    cpm = _cpm_days(project, early_finish)
    durations = monte_carlo_simulation(project, num_simulations=3000)
    p50 = statistics.median(durations)
    # within 40% — loose bound, just guards against gross drift
    assert abs(cpm - p50) / p50 < 0.4
