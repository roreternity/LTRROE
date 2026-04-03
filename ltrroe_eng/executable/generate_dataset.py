"""
Synthetic dataset generator for LTRROE project.
Generates multiple random projects with employees, tasks, dependencies,
and computes actual task durations using the core algorithms.
"""

import random
import pandas as pd
from datetime import datetime
from models import Project, Employee, Task, Dependency
from algorithms import (
    calculate_schedule,
    get_predecessors,
    get_successors,
    calculate_slowdown_factor
)

# Configuration
random.seed(27)                 # reproducible results
NUM_PROJECTS = 100               # number of projects to generate
MIN_TASKS = 5
MAX_TASKS = 30
MIN_EMPLOYEES = 3
MAX_EMPLOYEES = 15

# Pool of possible skills
SKILL_POOL = [
    "Python", "Java", "JavaScript", "C++", "SQL", "DevOps",
    "ML", "UI/UX", "testing", "architecture", "databases", "documentation"
]


def random_skills(max_skills=4):
    """Return a random subset of skills (size 1..max_skills)."""
    return random.sample(SKILL_POOL, k=random.randint(1, max_skills))


def random_efficiency(skills):
    """Generate a dictionary mapping each skill to a random efficiency (0.6..1.4)."""
    return {skill: round(random.uniform(0.6, 1.4), 2) for skill in skills}


def random_triple(low=1, high=30):
    """
    Generate a triangular distribution triplet (optimistic, likely, pessimistic)
    such that optimistic <= likely <= pessimistic.
    """
    a = random.randint(low, high - 2)
    b = random.randint(a, high - 1)
    c = random.randint(b, high)
    return (a, b, c)


def generate_dependencies(task_ids, density=0.3):
    """
    Generate random dependencies between tasks.
    Only forward dependencies (from earlier to later tasks) are created to avoid cycles.
    Returns a list of Dependency objects.
    """
    deps = []
    for i, from_id in enumerate(task_ids):
        for to_id in task_ids[i + 1:]:
            if random.random() < density:
                dep_type = random.choice(["FS", "SS", "FF", "SF"])
                lag = round(random.uniform(0, 3), 1)
                mandatory = random.choice([True, False])
                deps.append(Dependency(from_id, to_id, dep_type, lag, mandatory))
    return deps


def generate_project(proj_id):
    """
    Generate one complete project with employees, tasks, assignments and dependencies.
    Returns a list of feature dictionaries (one per task) that will form the dataset.
    """
    project = Project()
    project.proj_start_date = datetime.now()

    #  Create employees 
    num_employees = random.randint(MIN_EMPLOYEES, MAX_EMPLOYEES)
    for emp_id in range(num_employees):
        skills = random_skills(max_skills=4)
        emp = Employee(
            emp_id=emp_id,
            emp_name=f"Employee_{emp_id}",
            emp_skills=skills,
            emp_error_prob=round(random.uniform(0.05, 0.30), 2),
            emp_cost_per_hour=round(random.uniform(20.0, 80.0), 2),
            emp_efficiency=random_efficiency(skills)
        )
        emp.emp_max_daily_hours = random.uniform(4, 12)
        emp.emp_current_load = 0.0
        project.proj_employees[emp.emp_id] = emp

    # Create tasks 
    num_tasks = random.randint(MIN_TASKS, MAX_TASKS)
    for task_id in range(num_tasks):
        req_skills = random_skills(max_skills=3)
        task = Task(
            task_id=task_id,
            task_name=f"Task_{task_id}",
            task_skills=req_skills,
            task_crit=random.randint(1, 5),
            task_cost=round(random.uniform(100, 2000), 2),
            task_duration_dist=random_triple(2, 30)
        )
        project.proj_tasks[task.task_id] = task

    #  Assign employees to tasks
    for task in project.proj_tasks.values():
        # Candidates are employees that have at least one required skill
        candidates = [
            e for e in project.proj_employees.values()
            if set(task.task_skills) & set(e.emp_skills)
        ]
        if not candidates:
            candidates = list(project.proj_employees.values())
        num_assign = random.randint(1, min(3, len(candidates)))
        assigned = random.sample(candidates, num_assign)
        for emp in assigned:
            task.task_assigned_to.append(emp.emp_id)
            emp.emp_assigned_tasks.append(task.task_id)
            # Increase current load, but not above max
            load_inc = round(
                random.uniform(2, min(8, emp.emp_max_daily_hours - emp.emp_current_load)), 1
            )
            if load_inc > 0:
                emp.emp_current_load += load_inc

    #  Create dependencies 
    task_ids = list(project.proj_tasks.keys())
    project.proj_dependencies = generate_dependencies(task_ids, density=0.3)

    #  Compute schedule and task durations 
    early_start, early_finish, task_duration = calculate_schedule(project)

    #  Build feature vectors for each task 
    task_data = []
    for task_id, task in project.proj_tasks.items():
        actual_duration = task_duration[task_id]
        features = {
            'project_id': proj_id,
            'task_id': task_id,
            'planned_optimistic': task.task_duration_dist[0],
            'planned_likely': task.task_duration_dist[1],
            'planned_pessimistic': task.task_duration_dist[2],
            'criticality': task.task_crit,
            'cost': task.task_cost,
            'num_required_skills': len(task.task_skills),
            'num_assigned': len(task.task_assigned_to),
            'assigned_avg_efficiency': 0.0,
            'assigned_total_load': 0.0,
            'num_predecessors': len(get_predecessors(project, task_id)),
            'num_successors': len(get_successors(project, task_id)),
            'actual_duration': actual_duration
        }
        if task.task_assigned_to:
            eff_sum = 0
            count = 0
            total_load = 0.0
            for emp_id in task.task_assigned_to:
                emp = project.proj_employees[emp_id]
                total_load += emp.emp_current_load

                for skill in task.task_skills:
                    eff = emp.emp_efficiency.get(skill, 0.2)
                    eff_sum += eff
                    count += 1

            min_eff_per_emp = []
            for emp_id in task.task_assigned_to:
                emp = project.proj_employees[emp_id]
                effs = [emp.emp_efficiency.get(skill, 0.2) for skill in task.task_skills]
                if effs:
                    min_eff_per_emp.append(min(effs))

            miss_ratios = []
            for emp_id in task.task_assigned_to:
                emp = project.proj_employees[emp_id]
                missing = sum(1 for s in task.task_skills if s not in emp.emp_skills)
                miss_ratios.append(missing / len(task.task_skills) if task.task_skills else 0)

            primary_emp = project.proj_employees[task.task_assigned_to[0]]
            primary_effs = [primary_emp.emp_efficiency.get(s, 0.2) for s in task.task_skills]
            primary_missing = sum(1 for s in task.task_skills if s not in primary_emp.emp_skills)
            primary_emp = project.proj_employees[task.task_assigned_to[0]]
            primary_overload = max(0, primary_emp.emp_current_load - primary_emp.emp_max_daily_hours)
            primary_slowdown = calculate_slowdown_factor(primary_emp, task)
            task.task_primary_slowdown = primary_slowdown
            features['primary_slowdown'] = primary_slowdown

            features['primary_overload'] = primary_overload
            features['primary_min_efficiency'] = min(primary_effs) if primary_effs else 0.2
            features['primary_miss_ratio'] = primary_missing / len(task.task_skills) if task.task_skills else 0
            features['assigned_avg_miss_ratio'] = sum(miss_ratios) / len(miss_ratios) if miss_ratios else 0
            features['assigned_min_efficiency'] = min(min_eff_per_emp) if min_eff_per_emp else 0.2
            features['assigned_avg_efficiency'] = eff_sum / count if count > 0 else 0.2
            features['assigned_total_load'] = total_load

        task_data.append(features)  # ← вот чего не хватало

    return task_data

#  Main generation loop 
if __name__ == "__main__":
    all_tasks = []
    for proj_id in range(NUM_PROJECTS):
        task_data = generate_project(proj_id)
        all_tasks.extend(task_data)
        if (proj_id + 1) % 10 == 0:
            print(f"Generated {proj_id + 1} projects...")

    df = pd.DataFrame(all_tasks)
    df.to_csv('synthetic_tasks.csv', index=False)
    print(f"Dataset saved: {len(df)} tasks from {NUM_PROJECTS} projects.")
    print(df.head())