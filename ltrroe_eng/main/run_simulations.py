"""
Batch calculation of LTRROE metrics for all valid projects from a pickle file.
Output: metrics_results_full.csv and a console summary.
"""

import pickle
import csv
import random
import sys
from pathlib import Path
from statistics import mean, median, stdev
import ltrroe_objects
from ltrroe_objects import Dependency
from algorithms import calculate_schedule, calculate_backward_pass, monte_carlo_simulation

RANDOM_SEED     = 42
NUM_SIMULATIONS = 10000
MIN_TASKS       = 4
MIN_EMPLOYEES   = 1
FILES_DIR       = Path(__file__).resolve().parents[1] / "files"
PROJECTS_PKL    = FILES_DIR / "ltrroe_real_projects.pkl"
OUTPUT_CSV      = FILES_DIR / "metrics_results_full.csv"

random.seed(RANDOM_SEED)

# Loading
sys.modules.setdefault("models", ltrroe_objects)

with open(PROJECTS_PKL, "rb") as f:
    all_projects = pickle.load(f)
print(f"Loaded projects: {len(all_projects)}")

valid_projects = [
    p for p in all_projects.values()
    if len(p.proj_tasks) >= MIN_TASKS and len(p.proj_employees) >= MIN_EMPLOYEES
]
print(f"Valid projects:  {len(valid_projects)}")

# CSV fields
CSV_FIELDS = [
    "project_id",
    "n_tasks", "n_employees", "n_dependencies",
    "det_duration_days",
    "p10", "p50", "p90",
    "schedule_risk_ratio",   # (P90 - P50) / P50
    "det_vs_p50_delta",      # P50 - det_duration
    "critical_path_tasks",
    "avg_employee_efficiency",
    "mc_success",
    "error_msg",
]

results = []
errors  = []

def normalize_dependencies(project):
    """
    Return project dependencies as a list of Dependency objects.
    Older pickle files could store dependencies as a dictionary, a list, or
    unrelated values.
    """
    deps = project.proj_dependencies
    if isinstance(deps, dict):
        deps = list(deps.values())
    elif not isinstance(deps, list):
        deps = []

    clean_deps = [dep for dep in deps if isinstance(dep, Dependency)]
    project.proj_dependencies = clean_deps
    return clean_deps


def percentile(sorted_values, q: float):
    """Simple index-based quantile for an already sorted simulation list."""
    if not sorted_values:
        return None
    index = min(len(sorted_values) - 1, max(0, int(len(sorted_values) * q)))
    return sorted_values[index]

# Main loop
for idx, proj in enumerate(valid_projects, 1):
    pid = getattr(proj, 'proj_id', f"proj_{idx}")
    deps = normalize_dependencies(proj)
    row = {
        "project_id":    pid,
        "n_tasks":       len(proj.proj_tasks),
        "n_employees":   len(proj.proj_employees),
        "n_dependencies": len(deps),
        "mc_success":    False,
        "error_msg":     None,
    }

    try:
        # 1. Forward pass
        early_start, early_finish, task_duration = calculate_schedule(proj)
        det_duration = (max(early_finish.values()) - proj.proj_start_date).days
        row["det_duration_days"] = det_duration

        # 2. Backward pass + critical path
        late_start, late_finish = calculate_backward_pass(proj, early_finish, task_duration)
        cp_tasks = sum(
            1 for tid in proj.proj_tasks
            if tid in early_start and tid in late_start
            and (late_start[tid] - early_start[tid]).total_seconds() < 1
        )
        row["critical_path_tasks"] = cp_tasks

        # 3. Average team-efficiency proxy
        eff_values = [
            mean(emp.emp_efficiency.values())
            for emp in proj.proj_employees.values()
            if emp.emp_efficiency
        ]
        row["avg_employee_efficiency"] = round(mean(eff_values), 4) if eff_values else None

        # 4. Monte Carlo
        sims = monte_carlo_simulation(proj, num_simulations=NUM_SIMULATIONS)
        if sims:
            s = sorted(sims)
            # If all simulations returned the same duration, for example 0
            if s[0] == s[-1]:
                row["p10"] = row["p50"] = row["p90"] = s[0]
                row["schedule_risk_ratio"] = 0.0
                row["det_vs_p50_delta"] = s[0] - det_duration
                row["mc_success"] = True
            else:
                p10 = percentile(s, 0.10)
                p50 = percentile(s, 0.50)
                p90 = percentile(s, 0.90)
                row["p10"] = p10
                row["p50"] = p50
                row["p90"] = p90
                # Avoid division by zero
                if p50 and p50 > 1e-6:
                    row["schedule_risk_ratio"] = round((p90 - p50) / p50, 4)
                else:
                    row["schedule_risk_ratio"] = 0.0
                row["det_vs_p50_delta"] = p50 - det_duration
                row["mc_success"] = True
        if not sims:
            row["error_msg"] = "MC returned empty list"
            results.append(row)
            continue

    except Exception as e:
        row["error_msg"] = str(e)
        errors.append((pid, str(e)))
        for field in CSV_FIELDS:
            if field not in row:
                row[field] = None

    results.append(row)

print(f"\nTotal: {len(results)} projects, errors: {len(errors)}")

# Save output
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(results)
print(f"Saved: {OUTPUT_CSV}")

if errors:
    print(f"\nFirst 10 errors:")
    for pid, msg in errors[:10]:
        print(f"  {pid}: {msg}")

# Summary
ok = [r for r in results if r["mc_success"]]
print(f"\n{'='*60}")
print(f"SUMMARY  ({len(ok)} projects with successful MC out of {len(results)})")
print(f"{'='*60}")

def stat(label, vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return
    sd = f"  sd={stdev(vals):.2f}" if len(vals) > 1 else ""
    print(f"  {label:<35} "
          f"min={min(vals):.2f}  med={median(vals):.2f}  "
          f"mean={mean(vals):.2f}  max={max(vals):.2f}{sd}")

zero_p50_projects = [r["project_id"] for r in ok if r.get("p50") == 0]
if zero_p50_projects:
    print(f"Warning: projects with zero P50: {len(zero_p50_projects)}")
stat("Tasks per project",         [r["n_tasks"]               for r in ok])
stat("Employees",             [r["n_employees"]            for r in ok])
stat("Dependencies",            [r["n_dependencies"]         for r in ok])
stat("Det duration (days)",      [r["det_duration_days"]      for r in ok])
stat("P50 MC (days)",            [r["p50"]                    for r in ok])
stat("P90 MC (days)",            [r["p90"]                    for r in ok])
stat("Schedule risk ratio",     [r["schedule_risk_ratio"]    for r in ok])
stat("Det vs P50 delta (days)",  [r["det_vs_p50_delta"]       for r in ok])
stat("Avg employee efficiency", [r["avg_employee_efficiency"]for r in ok])
stat("Critical path tasks",     [r["critical_path_tasks"]    for r in ok])
