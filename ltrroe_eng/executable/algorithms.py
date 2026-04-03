"""
LTRROE Core Calculation Engine - Project Planning and Risk Analysis Algorithms
Implementation of forward/backward pass, Monte Carlo simulation, human factor modeling
"""
from datetime import timedelta
import random
from typing import Dict, List, Tuple

def build_dependency_cache(project):
    """
    Build dictionaries for quick lookup of predecessors and successors.
    Returns:
        predecessors_cache: dict task_id -> list of predecessor ids
        successors_cache:   dict task_id -> list of successor ids
    """
    predecessors_cache = {}
    successors_cache = {}
    for dep in project.proj_dependencies:
        # predecessors: for task `to` -> list of `from`
        if dep.dep_to_task not in predecessors_cache:
            predecessors_cache[dep.dep_to_task] = []
        predecessors_cache[dep.dep_to_task].append(dep.dep_from_task)

        # successors: for task `from` -> list of `to`
        if dep.dep_from_task not in successors_cache:
            successors_cache[dep.dep_from_task] = []
        successors_cache[dep.dep_from_task].append(dep.dep_to_task)

    return predecessors_cache, successors_cache


def get_predecessors(project, task_id, cache=None):
    """
    Return list of predecessor task ids for a given task.
    Uses cache if provided, otherwise scans the dependency list.
    """
    if cache is not None:
        return cache.get(task_id, [])
    preds = []
    for dep in project.proj_dependencies:
        if dep.dep_to_task == task_id:
            preds.append(dep.dep_from_task)
    return preds


def calculate_slowdown_factor(employee, task) -> float:
    """
    Calculate performance slowdown factor for employee on specific task.
    Based on skill mismatch and workload.
    """
    required_skills = task.task_skills
    employee_skills = employee.emp_skills

    # Check for missing skills
    missing_skills = [skill for skill in required_skills if skill not in employee_skills]
    missing_count = len(missing_skills)
    total_count = len(required_skills)

    # If all skills are missing
    if missing_count == total_count:
        return 3.0  # Extremely slow, unsuitable for task

    # If some skills are missing
    if missing_count > 0:
        missing_ratio = missing_count / total_count
        base_penalty = 2.0
        additional_penalty = missing_ratio * 1.0
        return base_penalty + additional_penalty

    # Find minimum efficiency across required skills
    efficiencies = []
    for skill in required_skills:
        # Get employee efficiency for this skill, default to 0.20 if not found
        efficiency = employee.emp_efficiency.get(skill, 0.20)
        efficiencies.append(efficiency)

    min_efficiency = min(efficiencies)

    # Skill‑based slowdown (inverse of efficiency)
    skill_slowdown = 1.0 / min_efficiency

    # Overload slowdown (if applicable)
    overload_slowdown = 1.0
    if employee.emp_current_load > employee.emp_max_daily_hours:
        overload = employee.emp_current_load - employee.emp_max_daily_hours
        overload_slowdown = 1.0 + (overload * 0.05)  # +5% per extra hour

    # Combined slowdown factor
    total_slowdown = skill_slowdown * overload_slowdown
    return total_slowdown


def calculate_task_duration(task, project=None) -> float:
    """
    Calculate task duration considering assigned employee performance.
    Uses PERT weighted average as baseline.
    """
    # Base duration (PERT weighted average)
    a, m, b = task.task_duration_dist
    base_duration = (a + 4 * m + b) / 6

    # If no project or no assignments, return base duration
    if project is None or not task.task_assigned_to:
        return base_duration

    # Safely get primary assignee
    try:
        primary_emp_id = task.task_assigned_to[0]
        employee = project.proj_employees.get(primary_emp_id)
        if employee is None:
            return base_duration
        slowdown = calculate_slowdown_factor(employee, task)
        return base_duration * slowdown
    except (IndexError, KeyError):
        return base_duration


def calculate_schedule(project) -> Tuple[Dict, Dict, Dict]:
    """
    Perform forward pass to calculate early start and finish dates.
    Returns:
        early_start  : dict task_id -> start date
        early_finish : dict task_id -> finish date
        task_duration: dict task_id -> duration in days
    """
    early_start = {}
    early_finish = {}
    task_duration = {}

    # Pre‑compute durations (may depend on assignments)
    for task_id, task in project.proj_tasks.items():
        task_duration[task_id] = calculate_task_duration(task, project)

    # Build cache for predecessors
    pred_cache, _ = build_dependency_cache(project)

    processed = set()
    max_iterations = len(project.proj_tasks) * 2
    iteration = 0

    # Process tasks until all are scheduled
    while len(processed) < len(project.proj_tasks) and iteration < max_iterations:
        iteration += 1
        something_done = False

        for task_id, task in project.proj_tasks.items():
            if task_id in processed:
                continue

            preds = get_predecessors(project, task_id, pred_cache)
            # Check if all predecessors are already processed
            if all(p in processed for p in preds):
                # Determine start date
                if not preds:
                    start_date = project.proj_start_date
                else:
                    max_finish = max(early_finish[p] for p in preds)
                    start_date = max_finish

                finish_date = start_date + timedelta(days=task_duration[task_id])

                early_start[task_id] = start_date
                early_finish[task_id] = finish_date
                processed.add(task_id)
                something_done = True

        # If nothing was processed in this iteration, we might have a cycle
        if not something_done:
            print(f"Warning: possible cyclic dependency. "
                  f"Processed {len(processed)} out of {len(project.proj_tasks)} tasks.")
            break

    if len(processed) < len(project.proj_tasks):
        print(f"Warning: schedule incomplete after {max_iterations} iterations. "
              f"Processed {len(processed)} tasks.")

    return early_start, early_finish, task_duration


def get_successors(project, task_id: int, cache=None) -> List[int]:
    """
    Return list of successor task ids for a given task.
    """
    if cache is not None:
        return cache.get(task_id, [])
    succs = []
    for dep in project.proj_dependencies:
        if dep.dep_from_task == task_id:
            succs.append(dep.dep_to_task)
    return succs


def calculate_backward_pass(project, early_finish: Dict, task_duration: Dict) -> Tuple[Dict, Dict]:
    """
    Perform backward pass to calculate late start and finish dates.
    Returns:
        late_start  : dict task_id -> latest start date
        late_finish : dict task_id -> latest finish date
    """
    late_start = {}
    late_finish = {}

    # Project deadline (assuming no contingency buffer)
    project_deadline = max(early_finish.values())

    # Build cache for successors
    _, succ_cache = build_dependency_cache(project)

    # Initialize late finish for terminal tasks (no successors)
    for task_id in project.proj_tasks.keys():
        succs = get_successors(project, task_id, succ_cache)
        if not succs:
            late_finish[task_id] = project_deadline

    # Process tasks in reverse order of early finish
    tasks_sorted = sorted(project.proj_tasks.items(),
                          key=lambda x: early_finish[x[0]],
                          reverse=True)

    for task_id, task in tasks_sorted:
        succs = get_successors(project, task_id, succ_cache)
        if succs:
            # Late finish = minimum late start among successors
            min_late_start = min(late_start.get(s, project_deadline) for s in succs)
            late_finish[task_id] = min_late_start

        # Late start = late finish - duration
        late_start[task_id] = late_finish[task_id] - timedelta(days=task_duration[task_id])

    return late_start, late_finish


def random_triangular(low: float, most_likely: float, high: float) -> float:
    """
    Generate random number from triangular distribution.
    Used for stochastic task durations.
    """
    u = random.random()
    if u == 0:
        return low
    elif u == 1:
        return high

    # Normalize most_likely to [0,1]
    c = (most_likely - low) / (high - low)

    if u < c:
        return low + (u * (high - low) * (most_likely - low)) ** 0.5
    else:
        return high - ((1 - u) * (high - low) * (high - most_likely)) ** 0.5


def forward_pass_with_random_duration(project, random_durations, pred_cache):
    """
    Perform forward pass using pre‑generated random durations.
    Returns early_finish dictionary for one simulation run.
    Handles possible cycles gracefully.
    """
    early_start = {}
    early_finish = {}
    processed = set()

    tasks_to_process = list(project.proj_tasks.keys())

    while tasks_to_process:
        task_processed = False

        # First, process tasks whose all predecessors are already done
        for task_id in tasks_to_process[:]:  # iterate over a copy
            preds = pred_cache.get(task_id, [])
            if all(pred in processed for pred in preds):
                # All predecessors processed → we can schedule this task
                if not preds:
                    start_date = project.proj_start_date
                else:
                    start_date = max(early_finish[p] for p in preds)

                duration = random_durations[task_id]
                finish_date = start_date + timedelta(days=duration)

                early_start[task_id] = start_date
                early_finish[task_id] = finish_date
                processed.add(task_id)
                tasks_to_process.remove(task_id)
                task_processed = True

        # If nothing could be processed normally, we have a cycle (or missing dependency)
        if not task_processed:
            # Pick the task with the fewest unprocessed predecessors as a heuristic
            def count_unprocessed(t):
                preds = pred_cache.get(t, [])
                return sum(1 for p in preds if p not in processed)

            task_id = min(tasks_to_process, key=count_unprocessed)
            # Use only already processed predecessors to compute start date
            processed_preds = [p for p in pred_cache.get(task_id, []) if p in processed]

            if not processed_preds:
                start_date = project.proj_start_date
            else:
                start_date = max(early_finish[p] for p in processed_preds)

            duration = random_durations[task_id]
            finish_date = start_date + timedelta(days=duration)

            early_start[task_id] = start_date
            early_finish[task_id] = finish_date
            processed.add(task_id)
            tasks_to_process.remove(task_id)
            # Optionally print a warning (commented by default)
            # print(f"Warning: cyclic dependency forced task {task_id} to start early.")

    return early_finish


def monte_carlo_simulation(project, num_simulations: int = 1000) -> List[float]:
    """
    Run Monte Carlo simulation for project risk assessment.
    Returns a list of total project durations (in days) for each simulation.
    Optimised by pre‑calculating slowdown factors and dependency cache.
    """
    project_durations = []
    task_slowdowns = {}

    # Pre‑calculate slowdown factor for each task (based on its primary assignee)
    for task_id, task in project.proj_tasks.items():
        if task.task_assigned_to and task.task_assigned_to[0] in project.proj_employees:
            emp_id = task.task_assigned_to[0]
            employee = project.proj_employees[emp_id]
            task_slowdowns[task_id] = calculate_slowdown_factor(employee, task)
        else:
            task_slowdowns[task_id] = 1.0

    # Build predecessor cache once
    pred_cache, _ = build_dependency_cache(project)

    for sim in range(num_simulations):
        random_durations = {}
        for task_id, task in project.proj_tasks.items():
            low, most_likely, high = task.task_duration_dist
            base_random = random_triangular(low, most_likely, high)
            adjusted_duration = base_random * task_slowdowns[task_id]
            random_durations[task_id] = adjusted_duration

        # Perform forward pass with these random durations
        early_finish = forward_pass_with_random_duration(project, random_durations, pred_cache)

        if early_finish:
            max_finish_date = max(early_finish.values())
            project_duration = (max_finish_date - project.proj_start_date).days
            project_durations.append(project_duration)

    return project_durations