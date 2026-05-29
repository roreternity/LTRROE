"""
LTRROE calculation core: scheduling and risk-analysis algorithms
Implements forward/backward passes, Monte Carlo simulation, and human-factor adjustments
"""

from datetime import timedelta
import random
from typing import Dict, List, Tuple

def _iter_dependencies(project):
    """
    Return dependencies regardless of whether they are stored as a list or a dictionary.
    """
    dependencies = project.proj_dependencies
    if isinstance(dependencies, dict):
        return dependencies.values()
    return dependencies

def get_predecessors(project, task_id: int) -> List[int]:
    """
    Find all task predecessors
    """
    preds = []
    for dep in _iter_dependencies(project):
        if dep.dep_to_task == task_id:
            preds.append(dep.dep_from_task)
    return preds

def calculate_slowdown_factor(employee, task) -> float:
    """
    Calculate the slowdown factor for an employee on a task
    Based on skill mismatch and workload.
    If efficiency is above 1, the multiplier drops below 1 and the task becomes faster.
    """
    required_skills = task.task_skills or []
    employee_skills = employee.emp_skills or []

    # Check missing skills
    missing_skills = [skill for skill in required_skills if skill not in employee_skills]
    missing_count = len(missing_skills)
    total_count = len(required_skills)

    # No skill penalty when the task has no required skills
    if total_count == 0:
        skill_slowdown = 1.0
    # All required skills are missing
    elif missing_count == total_count:
        skill_slowdown = 3.0  # Very slow; poor fit for the task

    # Some required skills are missing
    elif missing_count > 0:
        missing_ratio = missing_count / total_count
        base_penalty = 2.0

        # Base penalty of 2.0 plus an extra penalty for the missing-skill share
        additional_penalty = missing_ratio * 1.0
        skill_slowdown = base_penalty + additional_penalty
    else:
        # Find the minimum efficiency across required skills
        efficiencies = []
        for skill in required_skills:
            # Use the employee efficiency for this skill, defaulting to 0.20
            efficiency = (employee.emp_efficiency or {}).get(skill, 0.20)
            efficiencies.append(efficiency)
        
        min_efficiency = max(min(efficiencies), 0.01)
        
        # Skill slowdown factor
        skill_slowdown = 1.0 / min_efficiency
    
    # Overload slowdown factor, if any
    overload_slowdown = 1.0
    if employee.emp_current_load > employee.emp_max_daily_hours:
        overload = employee.emp_current_load - employee.emp_max_daily_hours
        # +5% for each excess hour
        overload_slowdown = 1.0 + (overload * 0.05)
    
    # Total slowdown factor
    total_slowdown = skill_slowdown * overload_slowdown
    
    return total_slowdown

def calculate_task_duration(task, project=None) -> float:
    """
    Calculate task duration adjusted for assignee performance
    Uses the PERT formula for the baseline estimate
    """
    # Baseline duration: PERT weighted average
    base_duration = (task.task_duration_dist[0] + task.task_duration_dist[1] * 4 + task.task_duration_dist[2]) / 6
    
    # Return baseline duration if the project or assignment is missing
    if project is None or not task.task_assigned_to:
        return base_duration
    
    # Safely get the primary assignee
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
    Run the forward pass to calculate early start and finish dates
    Returns early_start, early_finish, and task_duration dictionaries
    """
    task_duration = {}  # task_id -> duration in days
    
    # Calculate duration for each task
    for task_id, task in project.proj_tasks.items():
        task_duration[task_id] = calculate_task_duration(task, project)
    
    early_start, early_finish = _forward_pass(project, task_duration)
    
    return early_start, early_finish, task_duration

def _forward_pass(project, task_duration: Dict) -> Tuple[Dict, Dict]:
    """
    Shared forward pass for deterministic and random task durations.
    Returns early_start and early_finish dictionaries
    """
    early_start = {}  # task_id -> start date
    early_finish = {}  # task_id -> finish date
    processed = set()
    
    while len(processed) < len(project.proj_tasks):
        progress = False
        
        for task_id in project.proj_tasks.keys():
            if task_id in processed:
                continue
            
            # Find predecessors
            preds = get_predecessors(project, task_id)
            
            # Check whether this task can be processed
            if not preds or all(p in processed for p in preds):
                # Determine start date
                if not preds:
                    # No dependencies: start at the project start date
                    start_date = project.proj_start_date
                else:
                    # With dependencies: start after the latest predecessor finish
                    max_finish_date = max(early_finish[p] for p in preds)
                    start_date = max_finish_date
                
                # Calculate finish date
                duration_days = task_duration[task_id]
                finish_date = start_date + timedelta(days=duration_days)
                
                # Store results
                early_start[task_id] = start_date
                early_finish[task_id] = finish_date
                processed.add(task_id)
                progress = True
        
        if not progress:
            unresolved = sorted(set(project.proj_tasks) - processed)
            raise ValueError(
                "Cannot run the forward pass: check for cycles "
                f"or missing dependencies. Unresolved tasks: {unresolved}"
            )
    
    return early_start, early_finish

def get_successors(project, task_id: int) -> List[int]:
    """
    Find all task successors
    """
    successors = []
    for dep in _iter_dependencies(project):
        if dep.dep_from_task == task_id:
            successors.append(dep.dep_to_task)
    return successors

def calculate_backward_pass(project, early_finish: Dict, task_duration: Dict) -> Tuple[Dict, Dict]:
    """
    Run the backward pass to calculate late start and finish dates
    Returns late_start and late_finish dictionaries
    """
    late_start = {}
    late_finish = {}
    
    # Project deadline, without an additional buffer
    project_deadline = max(early_finish.values())
    
    # Initialize late-finish dates for terminal tasks
    for task_id in project.proj_tasks.keys():
        succs = get_successors(project, task_id)
        if not succs:
            late_finish[task_id] = project_deadline
    
    # Process tasks in descending early_finish order
    tasks_sorted = sorted(project.proj_tasks.items(), 
                         key=lambda x: early_finish[x[0]], 
                         reverse=True)
    
    for task_id, task in tasks_sorted:
        succs = get_successors(project, task_id)
        
        if succs:
            # Find the minimum late start among successors
            min_late_start = min(late_start.get(s, project_deadline) for s in succs)
            late_finish[task_id] = min_late_start
        
        # Calculate late start
        late_start[task_id] = late_finish[task_id] - timedelta(days=task_duration[task_id])
    
    return late_start, late_finish

def random_triangular(low: float, most_likely: float, high: float) -> float:
    """
    Generate a random value from a triangular distribution
    Used for PERT simulation
    """
    if high == low:
        return low
    if high < low:
        raise ValueError(f"Invalid triangular distribution: high ({high}) < low ({low})")
    if not low <= most_likely <= high:
        raise ValueError(
            "Invalid triangular distribution: "
            f"most_likely ({most_likely}) must be between low ({low}) and high ({high})"
        )
    
    u = random.random()
    
    if u == 0:
        return low
    elif u == 1:
        return high
    
    # Normalize most_likely
    c = (most_likely - low) / (high - low)
    
    if u < c:
        return low + (u * (high - low) * (most_likely - low)) ** 0.5
    else:
        return high - ((1 - u) * (high - low) * (high - most_likely)) ** 0.5

def forward_pass_with_random_duration(project, random_duration: Dict) -> Dict:
    """
    Run the forward pass with stochastic task durations
    Returns the early_finish dictionary for one simulation
    """
    _, early_finish = _forward_pass(project, random_duration)
    return early_finish

def build_task_slowdown_cache(project) -> Dict:
    """
    Precompute task slowdown using the primary assignee.
    This coefficient stays fixed inside Monte Carlo, so it does not need to be
    recomputed in every simulation.
    """
    task_slowdowns = {}

    for task_id, task in project.proj_tasks.items():
        slowdown = 1.0
        if task.task_assigned_to:
            primary_emp_id = task.task_assigned_to[0]
            employee = project.proj_employees.get(primary_emp_id)
            if employee:
                slowdown = calculate_slowdown_factor(employee, task)
        task_slowdowns[task_id] = slowdown

    return task_slowdowns

def monte_carlo_simulation(
    project,
    num_simulations: int = 1000,
    task_slowdowns: Dict = None
) -> List[float]:
    """
    Monte Carlo simulation for project-risk estimation
    Returns a list of project durations from all simulations
    """
    project_durations = []
    if task_slowdowns is None:
        task_slowdowns = build_task_slowdown_cache(project)
    
    for sim in range(num_simulations):
        random_durations = {}
        
        for task_id, task in project.proj_tasks.items():
            # Generate baseline random duration
            low, most_likely, high = task.task_duration_dist
            base_random = random_triangular(low, most_likely, high)
            
            # Adjust for assignee performance
            adjusted_duration = base_random * task_slowdowns.get(task_id, 1.0)
            
            random_durations[task_id] = adjusted_duration
        
        # Run the forward pass with random durations
        early_finish = forward_pass_with_random_duration(project, random_durations)
        
        if early_finish:
            max_finish_date = max(early_finish.values())
            project_duration = (max_finish_date - project.proj_start_date).days
            project_durations.append(project_duration)
    
    return project_durations
