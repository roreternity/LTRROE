"""
Imports real Gryzzly CSV data into LTRROE objects.
Builds projects, employees, tasks, and dependencies.
"""

import pandas as pd
import random
import pickle
import re
from pathlib import Path
from collections import defaultdict
from ltrroe_objects import Project, Employee, Task

# Configuration
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "real_datasets_gryzzly"
FILES_DIR = BASE_DIR / "files"
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

SKILL_POOL = [
    "Python", "Java", "JavaScript", "C++", "SQL", "DevOps",
    "ML", "UI/UX", "testing", "architecture", "databases", "documentation",
    "project management", "data analysis", "frontend", "backend"
]


_NS_PER_HOUR = 3_600_000_000_000  # nanoseconds to hours

def parse_duration_str(x) -> float:
    """Parse strings such as '1h30m15s' into hours for tasks_computed."""
    if pd.isna(x):
        return 0.0
    if isinstance(x, (int, float)):
        # tasks_computed can also provide a number; treat it as hours
        return float(x)
    x = str(x).strip().lower()
    if x in ("0s", "0", ""):
        return 0.0
    h = re.search(r'(\d+)h', x)
    m = re.search(r'(\d+)m(?!s)', x)
    s = re.search(r'(\d+)s', x)
    return (int(h.group(1)) if h else 0) + \
           (int(m.group(1)) if m else 0) / 60 + \
           (int(s.group(1)) if s else 0) / 3600

def parse_duration_ns(x) -> float:
    """Convert declaration durations from nanoseconds to hours."""
    if pd.isna(x):
        return 0.0
    return float(x) / _NS_PER_HOUR

_NULL_STRINGS = {'', 'null', 'none', 'nan', 'nat', 'n/a', 'na'}

def is_null_str(val) -> bool:
    """Return True for blank values and string-like nulls."""
    if pd.isna(val):
        return True
    return str(val).strip().lower() in _NULL_STRINGS


def normalize_id(value):
    """
    Normalize Gryzzly IDs to strings without losing compatibility.
    Parent IDs can appear as numeric values with `.0`; algorithms compare IDs directly.
    """
    if is_null_str(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def normalize_id_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Normalize ID columns that are present in the dataframe."""
    df = df.copy()
    for column in columns:
        if column in df.columns:
            df[column] = df[column].apply(normalize_id)
    return df


# ── CSV loading ──────────────────────────────────────────────────────────────
print("Loading CSV files...")
_NA = ['', 'null', 'NULL', 'None', 'NaN', 'nan', 'NA', 'N/A']
users             = pd.read_csv(DATA_DIR / "users.csv",             keep_default_na=True, na_values=_NA)
projects          = pd.read_csv(DATA_DIR / "projects.csv",          keep_default_na=True, na_values=_NA)
projects_computed = pd.read_csv(DATA_DIR / "projects_computed.csv", keep_default_na=True, na_values=_NA)
tasks             = pd.read_csv(DATA_DIR / "tasks.csv",             keep_default_na=True, na_values=_NA)
tasks_computed    = pd.read_csv(DATA_DIR / "tasks_computed.csv",    keep_default_na=True, na_values=_NA)
declarations      = pd.read_csv(DATA_DIR / "declarations.csv",      keep_default_na=True, na_values=_NA)

# Preprocessing ─────────────────────────────────────────────────────────────
users = normalize_id_columns(users, ["id", "team_id"])
projects = normalize_id_columns(projects, ["id"])
projects_computed = normalize_id_columns(projects_computed, ["id"])
tasks = normalize_id_columns(tasks, ["id", "project_id", "parent_id"])
tasks_computed = normalize_id_columns(tasks_computed, ["id"])
declarations = normalize_id_columns(declarations, ["id", "user_id", "task_id"])

# Deleted users are kept because they participated in historical tasks,
# and their declarations are real inputs for the efficiency proxy.
# The is_active flag keeps that distinction available if needed.
users = users.copy()
users['is_active'] = users['deleted_at'].isna()
print(f"Total users: {len(users)} "
      f"(active: {users['is_active'].sum()}, "
      f"deleted: {(~users['is_active']).sum()})")

# Merge tasks and projects with computed tables
tasks_full    = tasks.merge(tasks_computed, on='id', how='left', suffixes=('', '_computed'))
projects_full = projects.merge(projects_computed, on='id', how='left', suffixes=('', '_computed'))

# Parse task/project durations from strings such as "1h30m"
for df in (tasks_full, projects_full):
    df['planned_duration'] = df['planned_duration'].apply(parse_duration_str)
    df['elapsed_duration'] = df['elapsed_duration'].apply(parse_duration_str)

# declarations.duration is stored in nanoseconds, not as a duration string
declarations = declarations.copy()
declarations['duration'] = declarations['duration'].apply(parse_duration_ns)
print(f"Duration sample after parsing, hours: {declarations['duration'].head(3).tolist()}")

MIN_PROJECT_HOURS       = 1.0   # minimum 1 planned hour
MIN_TASK_HOURS          = 0.25  # minimum 15 minutes to keep PERT valid
MIN_PROJECT_DEPENDENCIES = 3    # projects without dependencies are not useful for CPM analysis
MAX_PROJECT_HOURS = 2000  # about 250 workdays at 8 hours per day
MAX_PROJECT_PLANNED_ELAPSED_RATIO = 2.0

# Initial project filter: both planned and elapsed durations must be positive
_candidate_projects = projects_full[
    (projects_full['planned_duration'] >= MIN_PROJECT_HOURS) &
    (projects_full['elapsed_duration'] >= MIN_PROJECT_HOURS) &
    (projects_full['planned_duration'] <= MAX_PROJECT_HOURS) &
    (projects_full['elapsed_duration'] <= MAX_PROJECT_HOURS) &
    (projects_full['planned_duration'] <= MAX_PROJECT_PLANNED_ELAPSED_RATIO * projects_full['elapsed_duration']) &
    (projects_full['elapsed_duration'] <= MAX_PROJECT_PLANNED_ELAPSED_RATIO * projects_full['planned_duration'])
]
_candidate_ids = set(_candidate_projects['id'])

# Group tasks by project once to avoid scanning the full task table
# for every project.
_valid_tasks = tasks_full[
    tasks_full['project_id'].isin(_candidate_ids) &
    (tasks_full['planned_duration'] >= MIN_TASK_HOURS)
]
_tasks_by_proj  = {pid: grp for pid, grp in _valid_tasks.groupby('project_id')}

# parent_id → child tasks for dependency checks
_all_tasks_by_proj = {pid: grp for pid, grp in
                      tasks_full[tasks_full['project_id'].isin(_candidate_ids)].groupby('project_id')}

valid_project_ids = []

for proj_id in _candidate_ids:
    proj_tasks = _tasks_by_proj.get(proj_id)
    if proj_tasks is None or len(proj_tasks) < 2:
        continue

    if (proj_tasks['planned_duration'] <= 0).any():
        continue

    task_ids    = set(proj_tasks['id'])
    all_p_tasks = _all_tasks_by_proj.get(proj_id)
    if all_p_tasks is None:
        continue

    deps = all_p_tasks[
        all_p_tasks['parent_id'].isin(task_ids) &
        all_p_tasks['id'].isin(task_ids)
    ]
    if len(deps) < MIN_PROJECT_DEPENDENCIES:
        continue

    valid_project_ids.append(proj_id)

n_proj_dropped = len(projects_full) - len(valid_project_ids)
print(f"Projects passing filters: {len(valid_project_ids)} of {len(projects_full)} "
      f"(dropped: {n_proj_dropped})")

# Convert valid_project_ids to a Series for reproducible sampling
valid_project_ids_s  = pd.Series(sorted(valid_project_ids))
sample_project_ids   = valid_project_ids_s.sample(min(5000, len(valid_project_ids_s)), random_state=RANDOM_SEED)
projects_full_sample = projects_full[projects_full['id'].isin(sample_project_ids)]

# Sample tasks are valid only; MIN_TASK_HOURS is already guaranteed, but keep the explicit filter
_proj_tasks       = tasks_full[tasks_full['project_id'].isin(sample_project_ids)]
tasks_full_sample = _proj_tasks[_proj_tasks['planned_duration'] >= MIN_TASK_HOURS]
n_task_dropped    = len(_proj_tasks) - len(tasks_full_sample)
print(f"Tasks excluded (planned_duration<{MIN_TASK_HOURS}h): {n_task_dropped}")

declarations_sample = declarations[declarations['task_id'].isin(tasks_full_sample['id'])]

print(f"Sample: {len(projects_full_sample)} projects, "
      f"{len(tasks_full_sample)} tasks, "
      f"{len(declarations_sample)} declarations")


# ── Helper functions ───────────────────────────────────────────────────

def build_primary_map(declarations_df: pd.DataFrame) -> dict:
    """
    Build a {task_id: primary_user_id} map using the user with the largest declared hours.
    Called once for the full dataset, not inside the employee loop.
    """
    grouped = declarations_df.groupby(['task_id', 'user_id'])['duration'].sum().reset_index()
    idx = grouped.groupby('task_id')['duration'].idxmax()
    primary = grouped.loc[idx].set_index('task_id')['user_id'].to_dict()
    return primary


def get_employee_efficiency(user_id, tasks_df: pd.DataFrame,
                            primary_map: dict) -> float:
    """
    Efficiency proxy = mean planned/elapsed ratio for tasks where the user is primary.
    Accepts a precomputed primary_map to avoid recalculating it inside the loop.
    """
    user_task_ids = [tid for tid, uid in primary_map.items() if uid == user_id]
    if not user_task_ids:
        return 1.0
    subset = tasks_df[tasks_df['id'].isin(user_task_ids)]
    ratios = []
    for _, row in subset.iterrows():
        p, e = row['planned_duration'], row['elapsed_duration']
        if p > 0 and e > 0:
            ratios.append(p / e)
    if not ratios:
        return 1.0
    return max(0.5, min(2.0, sum(ratios) / len(ratios)))


def assign_skills_to_user(_user_id) -> list:
    return random.sample(SKILL_POOL, random.randint(2, 4))


# ── Precompute primary_map once ──────────────────────────────────────────
primary_map = build_primary_map(declarations_sample)

# ── Build LTRROE objects ────────────────────────────────────────────────
# Iterate only over selected projects.
project_task_ids: dict[str, list[str]] = defaultdict(list)
for _, row in tasks_full_sample.iterrows():
    project_task_ids[row['project_id']].append(row['id'])

all_projects: dict = {}

print("Building projects...")
for proj_id, task_ids in project_task_ids.items():
    proj_info = projects_full_sample[projects_full_sample['id'] == proj_id]
    if proj_info.empty:
        continue

    proj_start      = pd.to_datetime(proj_info['created_at'].iloc[0])
    proj_planned_h  = proj_info['planned_duration'].iloc[0]
    proj_planned_days = max(proj_planned_h / 8.0, 1.0)  # fallback >= 1 day

    ltr_proj = Project(proj_id=proj_id)
    ltr_proj.proj_start_date = proj_start

    # Filter project declarations once
    proj_declarations = declarations_sample[declarations_sample['task_id'].isin(task_ids)]

    # ── Employees ────────────────────────────────────────────────────────────
    involved_user_ids = set(proj_declarations['user_id'].unique())
    employees_in_proj: dict = {}

    for uid in involved_user_ids:
        # Deleted users are still included because they are real historical actors.
        # user_row can be empty if uid is absent from users.csv.
        user_row  = users[users['id'] == uid]
        is_active = bool(user_row['is_active'].iloc[0]) if not user_row.empty else False

        eff_value = get_employee_efficiency(uid, tasks_full_sample, primary_map)
        skills    = assign_skills_to_user(uid)
        eff_dict  = {skill: eff_value for skill in skills}

        emp = Employee(
            emp_id=uid,
            emp_name=f"User_{uid}",
            emp_skills=skills,
            emp_error_prob=0.1,
            emp_cost_per_hour=30.0,
            emp_efficiency=eff_dict
        )
        emp.emp_current_load = 0.0
        emp.emp_is_active = is_active   # True = currently active, False = deleted/inactive
        employees_in_proj[uid] = emp
        ltr_proj.proj_employees[uid] = emp

    # ── Tasks ────────────────────────────────────────────────────────────────
    for task_id in task_ids:
        rows = tasks_full_sample[tasks_full_sample['id'] == task_id]
        if rows.empty:
            continue
        task_row    = rows.iloc[0]
        planned_h   = task_row['planned_duration']
        elapsed_h   = task_row['elapsed_duration']

        # 1. Drop rows without a useful duration estimate.
        if planned_h <= 0 and elapsed_h <= 0:
            continue

        # 2. Use elapsed duration as a surrogate if the planned estimate
        # is missing or too small.
        base_h = max(planned_h, elapsed_h, 0.25)  # minimum 15 minutes
        planned_days = base_h / 8.0

        # 3. Build a valid PERT triplet: pessimistic must be strictly above most likely.
        a = max(0.25, planned_days * 0.7)
        m = max(a, planned_days)
        b = max(m + 0.01, planned_days * 1.5)

        if   m > 20: crit = 5
        elif m > 10: crit = 4
        elif m > 5:  crit = 3
        elif m > 2:  crit = 2
        else:        crit = 1

        ltr_task = Task(
            task_id=task_id,
            task_name=f"Task_{task_id}",
            task_skills=[],
            task_crit=crit,
            task_cost=0.0,
            task_duration_dist=(a, m, b)
        )

        # Primary assignee from the precomputed map
        primary_uid = primary_map.get(task_id)
        if primary_uid is not None and primary_uid in employees_in_proj:
            ltr_task.task_assigned_to.append(primary_uid)
            employees_in_proj[primary_uid].emp_assigned_tasks.append(task_id)

        ltr_proj.proj_tasks[task_id] = ltr_task

    # ── Dependencies (parent → child) ─────────────────────────────────────────
    proj_tasks_df = tasks_full_sample[tasks_full_sample['project_id'] == proj_id]
    for _, row in proj_tasks_df.iterrows():
        parent = normalize_id(row.get('parent_id'))
        child  = normalize_id(row['id'])
        if parent and parent in ltr_proj.proj_tasks and child in ltr_proj.proj_tasks:
            ltr_proj.add_dependency(
                dep_from_task=parent,
                dep_to_task=child,
                dep_type="FS",
                dep_lag=0.0,
                dep_mandatory=True
            )

    # ── Current employee load ─────────────────────────────────────────
    for uid, emp in employees_in_proj.items():
        user_decl  = proj_declarations[proj_declarations['user_id'] == uid]
        total_hours = user_decl['duration'].sum()
        emp.emp_current_load = min(total_hours / proj_planned_days, 12.0)

    if len(ltr_proj.proj_dependencies) < MIN_PROJECT_DEPENDENCIES:
        continue

    all_projects[proj_id] = ltr_proj

    if len(all_projects) % 100 == 0:
        print(f"Processed projects: {len(all_projects)}")

print(f"Total projects built: {len(all_projects)}")

# Diagnostics for sampled projects that were not built
built_ids   = set(all_projects.keys())
sampled_ids = set(sample_project_ids)
lost_ids    = sampled_ids - built_ids
if lost_ids:
    print(f"\nSampled projects lost: {len(lost_ids)}")
    for pid in list(lost_ids)[:10]:
        proj_info = projects_full_sample[projects_full_sample['id'] == pid]
        n_tasks_raw   = len(tasks_full[tasks_full['project_id'] == pid])
        n_tasks_valid = len(tasks_full_sample[tasks_full_sample['project_id'] == pid])
        n_decl = len(declarations_sample[
            declarations_sample['task_id'].isin(
                tasks_full_sample[tasks_full_sample['project_id'] == pid]['id']
            )
        ])
        print(f"  {pid}: total tasks={n_tasks_raw}, "
              f"valid={n_tasks_valid}, declarations={n_decl}")

# ── Save output ────────────────────────────────────────────────────────────────
FILES_DIR.mkdir(parents=True, exist_ok=True)
output_file = FILES_DIR / "ltrroe_real_projects.pkl"
with open(output_file, "wb") as f:
    pickle.dump(all_projects, f)
print(f"Projects saved to {output_file}")

# ── Sanity-check ──────────────────────────────────────────────────────────────
if all_projects:
    sample_pid  = next(iter(all_projects))
    sample_proj = all_projects[sample_pid]
    print(f"\nSample project {sample_pid}:")
    print(f"  Employees:  {len(sample_proj.proj_employees)}")
    print(f"  Tasks:        {len(sample_proj.proj_tasks)}")
    print(f"  Dependencies: {len(sample_proj.proj_dependencies)}")
    print(f"  Start:       {sample_proj.proj_start_date}")
