"""
LTRROE Core Calculation Engine - Project Planning and Risk Analysis Algorithms
Implementation of forward/backward pass, Monte Carlo simulation, human factor modeling
"""

from test_data import create_test_project
from datetime import timedelta, datetime
import random
from typing import Dict, List, Tuple

def get_predecessors(project, task_id: int) -> List[int]:
    """
    Find all predecessor tasks for a given task
    """
    preds = []
    for dep in project.proj_dependencies:
        if dep.dep_to_task == task_id:
            preds.append(dep.dep_from_task)
    return preds

def calculate_slowdown_factor(employee, task) -> float:
    """
    Calculate performance slowdown factor for employee on specific task
    Based on skill mismatch and workload
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

        # Base 2.0 + additional for each missing skill
        additional_penalty = missing_ratio * 1.0
        return base_penalty + additional_penalty
    
    # Find minimum efficiency across required skills
    efficiencies = []
    for skill in required_skills:
        # Get employee efficiency for this skill, default to 0.20 if not found
        efficiency = employee.emp_efficiency.get(skill, 0.20)
        efficiencies.append(efficiency)
    
    min_efficiency = min(efficiencies)
    
    # Skill-based slowdown
    skill_slowdown = 1.0 / min_efficiency
    
    # Overload slowdown (if applicable)
    overload_slowdown = 1.0
    if employee.emp_current_load > employee.emp_max_daily_hours:
        overload = employee.emp_current_load - employee.emp_max_daily_hours
        # +5% for each extra hour
        overload_slowdown = 1.0 + (overload * 0.05)
    
    # Combined slowdown factor
    total_slowdown = skill_slowdown * overload_slowdown
    
    return total_slowdown

def calculate_task_duration(task, project=None) -> float:
    """
    Calculate task duration considering assigned employee performance
    Uses PERT formula for base estimation
    """
    # Base duration (PERT weighted average)
    base_duration = (task.task_duration_dist[0] + task.task_duration_dist[1] * 4 + task.task_duration_dist[2]) / 6
    
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
    Perform forward pass to calculate early start and finish dates
    Returns: early_start, early_finish, task_duration dictionaries
    """
    early_start = {}  # task_id -> start date
    early_finish = {}  # task_id -> finish date
    task_duration = {}  # task_id -> duration in days
    
    # Calculate duration for each task
    for task_id, task in project.proj_tasks.items():
        task_duration[task_id] = calculate_task_duration(task, project)
    
    # Process tasks until all are scheduled
    processed = set()
    
    while len(processed) < len(project.proj_tasks):
        for task_id, task in project.proj_tasks.items():
            if task_id in processed:
                continue
            
            # Find predecessors
            preds = get_predecessors(project, task_id)
            
            # Check if task can be processed
            if not preds or all(p in processed for p in preds):
                # Determine start date
                if not preds:
                    # No dependencies → start at project start
                    start_date = project.proj_start_date
                else:
                    # Dependencies exist → start after last predecessor finishes
                    max_finish_date = max(early_finish[p] for p in preds)
                    start_date = max_finish_date
                
                # Calculate finish date
                duration_days = task_duration[task_id]
                finish_date = start_date + timedelta(days=duration_days)
                
                # Store results
                early_start[task_id] = start_date
                early_finish[task_id] = finish_date
                processed.add(task_id)
    
    return early_start, early_finish, task_duration

def get_successors(project, task_id: int) -> List[int]:
    """
    Find all successor tasks for a given task
    """
    successors = []
    for dep in project.proj_dependencies:
        if dep.dep_from_task == task_id:
            successors.append(dep.dep_to_task)
    return successors

def calculate_backward_pass(project, early_finish: Dict, task_duration: Dict) -> Tuple[Dict, Dict]:
    """
    Perform backward pass to calculate late start and finish dates
    Returns: late_start, late_finish dictionaries
    """
    late_start = {}
    late_finish = {}
    
    # Project deadline (assume no contingency buffer)
    project_deadline = max(early_finish.values())
    
    # Initialize late finish for terminal tasks
    for task_id in project.proj_tasks.keys():
        succs = get_successors(project, task_id)
        if not succs:
            late_finish[task_id] = project_deadline
    
    # Process tasks in reverse order of early finish
    tasks_sorted = sorted(project.proj_tasks.items(), 
                         key=lambda x: early_finish[x[0]], 
                         reverse=True)
    
    for task_id, task in tasks_sorted:
        succs = get_successors(project, task_id)
        
        if succs:
            # Find minimum late start among successors
            min_late_start = min(late_start.get(s, project_deadline) for s in succs)
            late_finish[task_id] = min_late_start
        
        # Calculate late start
        late_start[task_id] = late_finish[task_id] - timedelta(days=task_duration[task_id])
    
    return late_start, late_finish

def random_triangular(low: float, most_likely: float, high: float) -> float:
    """
    Generate random number from triangular distribution
    Used for PERT simulation
    """
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
    Perform forward pass with stochastic task durations
    Returns: early_finish dictionary for single simulation run
    """
    early_start = {}
    early_finish = {}
    processed = set()
    
    while len(processed) < len(project.proj_tasks):
        for task_id, task in project.proj_tasks.items():
            if task_id in processed:
                continue
            
            preds = get_predecessors(project, task_id)
            
            if not preds or all(p in processed for p in preds):
                if not preds:
                    start_date = project.proj_start_date
                else:
                    max_finish_date = max(early_finish[p] for p in preds)
                    start_date = max_finish_date
                
                duration_days = random_duration[task_id]
                finish_date = start_date + timedelta(days=duration_days)
                
                early_start[task_id] = start_date
                early_finish[task_id] = finish_date
                processed.add(task_id)
    
    return early_finish

def monte_carlo_simulation(project, num_simulations: int = 1000) -> List[float]:
    """
    Monte Carlo simulation for project risk assessment
    Returns: List of project durations from all simulations
    """
    project_durations = []
    
    for sim in range(num_simulations):
        random_durations = {}
        
        for task_id, task in project.proj_tasks.items():
            # Generate base random duration
            low, most_likely, high = task.task_duration_dist
            base_random = random_triangular(low, most_likely, high)
            
            # Adjust for employee performance
            if task.task_assigned_to:
                primary_emp_id = task.task_assigned_to[0]
                employee = project.proj_employees.get(primary_emp_id)
                if employee:
                    slowdown = calculate_slowdown_factor(employee, task)
                    adjusted_duration = base_random * slowdown
                else:
                    adjusted_duration = base_random
            else:
                adjusted_duration = base_random
            
            random_durations[task_id] = adjusted_duration
        
        # Perform forward pass with random durations
        early_finish = forward_pass_with_random_duration(project, random_durations)
        
        if early_finish:
            max_finish_date = max(early_finish.values())
            project_duration = (max_finish_date - project.proj_start_date).days
            project_durations.append(project_duration)
    
    return project_durations
