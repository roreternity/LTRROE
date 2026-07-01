"""
Генератор синтетического датасета LTRROE на уровне проектов.

Выходной CSV совместим по основным колонкам с metrics_results_full.csv:
одна строка = один проект, а не одна задача.
"""

import argparse
import csv
import random
from datetime import datetime
from pathlib import Path
from ltrroe.paths import FILES_DIR, figures
from statistics import mean

from ltrroe.core.objects import Project, Employee, Task, Dependency
from ltrroe.core.algorithms import (
    calculate_backward_pass,
    calculate_schedule,
    monte_carlo_simulation,
)


RANDOM_SEED = 27
NUM_PROJECTS = 10000
NUM_SIMULATIONS = 10000
MIN_TASKS = 3
MAX_TASKS = 30
MIN_EMPLOYEES = 3
MAX_EMPLOYEES = 15
MIN_DEPENDENCIES = 3

OUTPUT_CSV = FILES_DIR / "synthetic_project_metrics.csv"

SKILL_POOL = [
    "Python", "Java", "JavaScript", "C++", "SQL", "DevOps",
    "ML", "UI/UX", "testing", "architecture", "databases", "documentation",
]

CSV_FIELDS = [
    "project_id",
    "n_tasks", "n_employees", "n_dependencies",
    "det_duration_days",
    "p10", "p50", "p90",
    "schedule_risk_ratio",
    "det_vs_p50_delta",
    "critical_path_tasks",
    "avg_employee_efficiency",
    "mc_success",
    "error_msg",
]


def random_skills(max_skills=4):
    return random.sample(SKILL_POOL, k=random.randint(1, max_skills))


def random_efficiency(skills):
    return {skill: round(random.uniform(0.6, 1.4), 2) for skill in skills}


def random_triple(low=1.0, high=18.0):
    """PERT-триплет в днях: optimistic <= likely <= pessimistic."""
    optimistic = round(random.uniform(low, high * 0.65), 2)
    likely = round(random.uniform(optimistic, high * 0.9), 2)
    pessimistic = round(random.uniform(likely + 0.1, high), 2)
    return optimistic, likely, pessimistic


def generate_dependencies(task_ids, min_dependencies=MIN_DEPENDENCIES):
    """Случайный DAG: зависимости только от меньшего task_id к большему."""
    possible_edges = [
        (from_id, to_id)
        for i, from_id in enumerate(task_ids)
        for to_id in task_ids[i + 1:]
    ]
    max_edges = len(possible_edges)
    if max_edges < min_dependencies:
        return []

    upper = min(max_edges, max(min_dependencies, round(len(task_ids) * random.uniform(0.6, 1.4))))
    n_dependencies = random.randint(min_dependencies, upper)
    sampled_edges = random.sample(possible_edges, n_dependencies)

    return [
        Dependency(
            dep_from_task=from_id,
            dep_to_task=to_id,
            dep_type="FS",
            dep_lag=0.0,
            dep_mandatory=True,
        )
        for from_id, to_id in sampled_edges
    ]


def generate_project(proj_id):
    project = Project(proj_id=f"synth_{proj_id}")
    project.proj_start_date = datetime(2026, 1, 1)

    for emp_id in range(random.randint(MIN_EMPLOYEES, MAX_EMPLOYEES)):
        skills = random_skills(max_skills=4)
        emp = Employee(
            emp_id=emp_id,
            emp_name=f"Employee_{emp_id}",
            emp_skills=skills,
            emp_error_prob=round(random.uniform(0.05, 0.30), 2),
            emp_cost_per_hour=round(random.uniform(20.0, 80.0), 2),
            emp_efficiency=random_efficiency(skills),
        )
        emp.emp_max_daily_hours = random.uniform(4, 12)
        emp.emp_current_load = 0.0
        project.proj_employees[emp.emp_id] = emp

    for task_id in range(random.randint(MIN_TASKS, MAX_TASKS)):
        task = Task(
            task_id=task_id,
            task_name=f"Task_{task_id}",
            task_skills=random_skills(max_skills=3),
            task_crit=random.randint(1, 5),
            task_cost=round(random.uniform(100, 2000), 2),
            task_duration_dist=random_triple(),
        )
        project.proj_tasks[task.task_id] = task

    employees = list(project.proj_employees.values())
    for task in project.proj_tasks.values():
        candidates = [
            emp for emp in employees
            if set(task.task_skills) & set(emp.emp_skills)
        ] or employees

        assigned = random.sample(candidates, random.randint(1, min(3, len(candidates))))
        for emp in assigned:
            task.task_assigned_to.append(emp.emp_id)
            emp.emp_assigned_tasks.append(task.task_id)
            emp.emp_current_load += round(random.uniform(1.0, 5.0), 1)

    project.proj_dependencies = generate_dependencies(list(project.proj_tasks.keys()))
    return project


def percentile(sorted_values, q):
    if not sorted_values:
        return None
    idx = min(len(sorted_values) - 1, max(0, int(len(sorted_values) * q)))
    return sorted_values[idx]


def project_to_metrics(project, num_simulations):
    row = {
        "project_id": getattr(project, "proj_id", None),
        "n_tasks": len(project.proj_tasks),
        "n_employees": len(project.proj_employees),
        "n_dependencies": len(project.proj_dependencies),
        "mc_success": False,
        "error_msg": None,
    }

    try:
        early_start, early_finish, task_duration = calculate_schedule(project)
        det_duration = (max(early_finish.values()) - project.proj_start_date).days
        row["det_duration_days"] = det_duration

        late_start, _ = calculate_backward_pass(project, early_finish, task_duration)
        row["critical_path_tasks"] = sum(
            1 for tid in project.proj_tasks
            if tid in early_start and tid in late_start
            and (late_start[tid] - early_start[tid]).total_seconds() < 1
        )

        eff_values = [
            mean(emp.emp_efficiency.values())
            for emp in project.proj_employees.values()
            if emp.emp_efficiency
        ]
        row["avg_employee_efficiency"] = round(mean(eff_values), 4) if eff_values else None

        sims = monte_carlo_simulation(project, num_simulations=num_simulations)
        if not sims:
            row["error_msg"] = "MC returned empty list"
            return row

        sorted_sims = sorted(sims)
        p10 = percentile(sorted_sims, 0.10)
        p50 = percentile(sorted_sims, 0.50)
        p90 = percentile(sorted_sims, 0.90)

        row["p10"] = p10
        row["p50"] = p50
        row["p90"] = p90
        row["schedule_risk_ratio"] = round((p90 - p50) / p50, 4) if p50 else 0.0
        row["det_vs_p50_delta"] = p50 - det_duration
        row["mc_success"] = True
        return row

    except Exception as exc:
        row["error_msg"] = str(exc)
        return row


def build_dataset(num_projects, num_simulations, output_csv):
    rows = []
    attempts = 0
    ok = 0

    while len(rows) < num_projects:
        attempts += 1
        project = generate_project(attempts)
        if len(project.proj_dependencies) < MIN_DEPENDENCIES:
            continue

        row = project_to_metrics(project, num_simulations)
        rows.append(row)
        if row["mc_success"]:
            ok += 1
        if len(rows) % 100 == 0 or len(rows) == num_projects:
            print(f"  [{len(rows)}/{num_projects}] успешно={ok}")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    ok_rows = [row for row in rows if row["mc_success"]]
    print(f"\nСохранено: {output_csv}")
    print(f"Итого: {len(rows)} проектов, успешный МК: {len(ok_rows)}")
    if ok_rows:
        print(
            "Schedule risk ratio: "
            f"mean={mean(row['schedule_risk_ratio'] for row in ok_rows):.3f}, "
            f"median={sorted(row['schedule_risk_ratio'] for row in ok_rows)[len(ok_rows)//2]:.3f}"
        )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-projects", type=int, default=NUM_PROJECTS)
    parser.add_argument("--num-simulations", type=int, default=NUM_SIMULATIONS)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--output", type=Path, default=OUTPUT_CSV)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    random.seed(args.seed)
    build_dataset(args.num_projects, args.num_simulations, args.output)
