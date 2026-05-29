"""
Батч-расчёт метрик LTRROE по всем валидным проектам из pkl.
Выход: metrics_results_full.csv + сводка в stdout.
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

# Загрузка
sys.modules.setdefault("models", ltrroe_objects)

with open(PROJECTS_PKL, "rb") as f:
    all_projects = pickle.load(f)
print(f"Загружено проектов: {len(all_projects)}")

valid_projects = [
    p for p in all_projects.values()
    if len(p.proj_tasks) >= MIN_TASKS and len(p.proj_employees) >= MIN_EMPLOYEES
]
print(f"Валидных проектов:  {len(valid_projects)}")

# CSV-поля
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
    Вернуть зависимости проекта как список объектов Dependency.
    Старые pickle-файлы могли хранить зависимости словарём, списком или
    посторонними значениями.
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
    """Простой индексный квантиль для уже отсортированного списка симуляций."""
    if not sorted_values:
        return None
    index = min(len(sorted_values) - 1, max(0, int(len(sorted_values) * q)))
    return sorted_values[index]

# Основной цикл
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

        # 2. Backward pass + критический путь
        late_start, late_finish = calculate_backward_pass(proj, early_finish, task_duration)
        cp_tasks = sum(
            1 for tid in proj.proj_tasks
            if tid in early_start and tid in late_start
            and (late_start[tid] - early_start[tid]).total_seconds() < 1
        )
        row["critical_path_tasks"] = cp_tasks

        # 3. Средняя эффективность команды
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
            # Если все симуляции дали одинаковую длительность (например, 0)
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
                # Защита от деления на ноль
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

print(f"\nИтого: {len(results)} проектов, ошибок: {len(errors)}")

# Сохранение
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(results)
print(f"Сохранено: {OUTPUT_CSV}")

if errors:
    print(f"\nПервые 10 ошибок:")
    for pid, msg in errors[:10]:
        print(f"  {pid}: {msg}")

# Сводка
ok = [r for r in results if r["mc_success"]]
print(f"\n{'='*60}")
print(f"СВОДКА  ({len(ok)} проектов с успешным МК из {len(results)})")
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
    print(f"Предупреждение: проектов с нулевым P50: {len(zero_p50_projects)}")
stat("Задач на проект",         [r["n_tasks"]               for r in ok])
stat("Сотрудников",             [r["n_employees"]            for r in ok])
stat("Зависимостей",            [r["n_dependencies"]         for r in ok])
stat("Det duration (дни)",      [r["det_duration_days"]      for r in ok])
stat("P50 МК (дни)",            [r["p50"]                    for r in ok])
stat("P90 МК (дни)",            [r["p90"]                    for r in ok])
stat("Schedule risk ratio",     [r["schedule_risk_ratio"]    for r in ok])
stat("Det vs P50 delta (дни)",  [r["det_vs_p50_delta"]       for r in ok])
stat("Avg employee efficiency", [r["avg_employee_efficiency"]for r in ok])
stat("Critical path tasks",     [r["critical_path_tasks"]    for r in ok])
