"""
Импорт реальных данных из CSV Gryzzly в объекты LTRROE.
Строит проекты, сотрудников, задачи и зависимости.
"""

import pandas as pd
import random
import pickle
import re
from pathlib import Path
from collections import defaultdict
from ltrroe_objects import Project, Employee, Task

# Конфигурация
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


_NS_PER_HOUR = 3_600_000_000_000  # наносекунды → часы

def parse_duration_str(x) -> float:
    """Парсит строки вида '1h30m15s' в часы (для tasks_computed)."""
    if pd.isna(x):
        return 0.0
    if isinstance(x, (int, float)):
        # tasks_computed тоже может отдать число — трактуем как часы
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
    """Конвертирует наносекунды (int64 из declarations) в часы."""
    if pd.isna(x):
        return 0.0
    return float(x) / _NS_PER_HOUR

_NULL_STRINGS = {'', 'null', 'none', 'nan', 'nat', 'n/a', 'na'}

def is_null_str(val) -> bool:
    """True если значение — пустая строка или строковый null."""
    if pd.isna(val):
        return True
    return str(val).strip().lower() in _NULL_STRINGS


def normalize_id(value):
    """
    Привести ID из Gryzzly к строке без потери совместимости.
    В CSV родительские ID иногда приходят как числа с `.0`, а алгоритмы сравнивают ID напрямую.
    """
    if is_null_str(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def normalize_id_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Нормализовать ID-колонки, которые реально есть в датафрейме."""
    df = df.copy()
    for column in columns:
        if column in df.columns:
            df[column] = df[column].apply(normalize_id)
    return df


# ── Загрузка CSV ──────────────────────────────────────────────────────────────
print("Загрузка CSV...")
_NA = ['', 'null', 'NULL', 'None', 'NaN', 'nan', 'NA', 'N/A']
users             = pd.read_csv(DATA_DIR / "users.csv",             keep_default_na=True, na_values=_NA)
projects          = pd.read_csv(DATA_DIR / "projects.csv",          keep_default_na=True, na_values=_NA)
projects_computed = pd.read_csv(DATA_DIR / "projects_computed.csv", keep_default_na=True, na_values=_NA)
tasks             = pd.read_csv(DATA_DIR / "tasks.csv",             keep_default_na=True, na_values=_NA)
tasks_computed    = pd.read_csv(DATA_DIR / "tasks_computed.csv",    keep_default_na=True, na_values=_NA)
declarations      = pd.read_csv(DATA_DIR / "declarations.csv",      keep_default_na=True, na_values=_NA)

# Предобработка ─────────────────────────────────────────────────────────────
users = normalize_id_columns(users, ["id", "team_id"])
projects = normalize_id_columns(projects, ["id"])
projects_computed = normalize_id_columns(projects_computed, ["id"])
tasks = normalize_id_columns(tasks, ["id", "project_id", "parent_id"])
tasks_computed = normalize_id_columns(tasks_computed, ["id"])
declarations = normalize_id_columns(declarations, ["id", "user_id", "task_id"])

# Все пользователи — удалённые тоже участвовали в исторических задачах,
# их декларации реальны и нужны для расчёта эффективности.
# Флаг is_active позволяет различать при необходимости.
users = users.copy()
users['is_active'] = users['deleted_at'].isna()
print(f"Пользователей всего: {len(users)} "
      f"(активных: {users['is_active'].sum()}, "
      f"удалённых: {(~users['is_active']).sum()})")

# Объединяем задачи и проекты с computed-данными
tasks_full    = tasks.merge(tasks_computed, on='id', how='left', suffixes=('', '_computed'))
projects_full = projects.merge(projects_computed, on='id', how='left', suffixes=('', '_computed'))

# Парсим длительности задач/проектов (строки "1h30m")
for df in (tasks_full, projects_full):
    df['planned_duration'] = df['planned_duration'].apply(parse_duration_str)
    df['elapsed_duration'] = df['elapsed_duration'].apply(parse_duration_str)

# duration в declarations хранится в наносекундах, а не в строковом формате
declarations = declarations.copy()
declarations['duration'] = declarations['duration'].apply(parse_duration_ns)
print(f"Пример duration после парсинга (часы): {declarations['duration'].head(3).tolist()}")

MIN_PROJECT_HOURS       = 1.0   # минимум 1 час плановой работы
MIN_TASK_HOURS          = 0.25  # минимум 15 минут (иначе PERT: деление на 0)
MIN_PROJECT_DEPENDENCIES = 3    # проекты без зависимостей не интересны для CPM
MAX_PROJECT_HOURS = 2000  # около 250 рабочих дней при 8-часовом дне
MAX_PROJECT_PLANNED_ELAPSED_RATIO = 2.0

# Предварительный фильтр по проектам: плановая И фактическая длительность > 0
_candidate_projects = projects_full[
    (projects_full['planned_duration'] >= MIN_PROJECT_HOURS) &
    (projects_full['elapsed_duration'] >= MIN_PROJECT_HOURS) &
    (projects_full['planned_duration'] <= MAX_PROJECT_HOURS) &
    (projects_full['elapsed_duration'] <= MAX_PROJECT_HOURS) &
    (projects_full['planned_duration'] <= MAX_PROJECT_PLANNED_ELAPSED_RATIO * projects_full['elapsed_duration']) &
    (projects_full['elapsed_duration'] <= MAX_PROJECT_PLANNED_ELAPSED_RATIO * projects_full['planned_duration'])
]
_candidate_ids = set(_candidate_projects['id'])

# Группируем задачи по проекту один раз, чтобы не выполнять полный проход по
# таблице задач для каждого проекта.
_valid_tasks = tasks_full[
    tasks_full['project_id'].isin(_candidate_ids) &
    (tasks_full['planned_duration'] >= MIN_TASK_HOURS)
]
_tasks_by_proj  = {pid: grp for pid, grp in _valid_tasks.groupby('project_id')}

# parent_id → child tasks для проверки зависимостей
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
print(f"Проектов прошло фильтр: {len(valid_project_ids)} из {len(projects_full)} "
      f"(отброшено: {n_proj_dropped})")

# valid_project_ids — list, конвертируем в Series для воспроизводимой выборки
valid_project_ids_s  = pd.Series(sorted(valid_project_ids))
sample_project_ids   = valid_project_ids_s.sample(min(5000, len(valid_project_ids_s)), random_state=RANDOM_SEED)
projects_full_sample = projects_full[projects_full['id'].isin(sample_project_ids)]

# Задачи выборки — только валидные (MIN_TASK_HOURS уже гарантирован выше, но фильтруем явно)
_proj_tasks       = tasks_full[tasks_full['project_id'].isin(sample_project_ids)]
tasks_full_sample = _proj_tasks[_proj_tasks['planned_duration'] >= MIN_TASK_HOURS]
n_task_dropped    = len(_proj_tasks) - len(tasks_full_sample)
print(f"Задач исключено (planned_duration<{MIN_TASK_HOURS}ч): {n_task_dropped}")

declarations_sample = declarations[declarations['task_id'].isin(tasks_full_sample['id'])]

print(f"Выборка: {len(projects_full_sample)} проектов, "
      f"{len(tasks_full_sample)} задач, "
      f"{len(declarations_sample)} деклараций")


# ── Вспомогательные функции ───────────────────────────────────────────────────

def build_primary_map(declarations_df: pd.DataFrame) -> dict:
    """
    Строит словарь {task_id: primary_user_id} — исполнитель с макс. суммой часов.
    Вызывается один раз на весь датасет, а не внутри цикла по сотрудникам.
    """
    grouped = declarations_df.groupby(['task_id', 'user_id'])['duration'].sum().reset_index()
    idx = grouped.groupby('task_id')['duration'].idxmax()
    primary = grouped.loc[idx].set_index('task_id')['user_id'].to_dict()
    return primary


def get_employee_efficiency(user_id, tasks_df: pd.DataFrame,
                            primary_map: dict) -> float:
    """
    Эффективность = среднее (planned / elapsed) по задачам, где user — primary
    Принимает готовый primary_map, чтобы не пересчитывать его внутри цикла.
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


# ── Предрасчёт primary_map один раз ──────────────────────────────────────────
primary_map = build_primary_map(declarations_sample)

# ── Построение объектов LTRROE ────────────────────────────────────────────────
# Итерируем только по отобранным проектам.
project_task_ids: dict[str, list[str]] = defaultdict(list)
for _, row in tasks_full_sample.iterrows():
    project_task_ids[row['project_id']].append(row['id'])

all_projects: dict = {}

print("Построение проектов...")
for proj_id, task_ids in project_task_ids.items():
    proj_info = projects_full_sample[projects_full_sample['id'] == proj_id]
    if proj_info.empty:
        continue

    proj_start      = pd.to_datetime(proj_info['created_at'].iloc[0])
    proj_planned_h  = proj_info['planned_duration'].iloc[0]
    proj_planned_days = max(proj_planned_h / 8.0, 1.0)  # fallback ≥ 1 день

    ltr_proj = Project(proj_id=proj_id)
    ltr_proj.proj_start_date = proj_start

    # Декларации проекта — фильтруем один раз
    proj_declarations = declarations_sample[declarations_sample['task_id'].isin(task_ids)]

    # ── Сотрудники ────────────────────────────────────────────────────────────
    involved_user_ids = set(proj_declarations['user_id'].unique())
    employees_in_proj: dict = {}

    for uid in involved_user_ids:
        # Удалённые пользователи тоже участвуют — они реальные исторические акторы.
        # user_row может быть пустым если uid вообще нет в users.csv (edge case).
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
        emp.emp_is_active = is_active   # True = работает сейчас, False = уволен/удалён
        employees_in_proj[uid] = emp
        ltr_proj.proj_employees[uid] = emp

    # ── Задачи ────────────────────────────────────────────────────────────────
    for task_id in task_ids:
        rows = tasks_full_sample[tasks_full_sample['id'] == task_id]
        if rows.empty:
            continue
        task_row    = rows.iloc[0]
        planned_h   = task_row['planned_duration']
        elapsed_h   = task_row['elapsed_duration']

        # 1. Отбрасываем строки без полезной оценки длительности.
        if planned_h <= 0 and elapsed_h <= 0:
            continue

        # 2. Используем фактическую длительность как суррогат, если плановая
        # оценка отсутствует или слишком мала.
        base_h = max(planned_h, elapsed_h, 0.25)  # минимум 15 минут
        planned_days = base_h / 8.0

        # 3. Строим корректный PERT-триплет: pessimistic строго больше most likely.
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

        # Основной исполнитель из предрасчитанной карты
        primary_uid = primary_map.get(task_id)
        if primary_uid is not None and primary_uid in employees_in_proj:
            ltr_task.task_assigned_to.append(primary_uid)
            employees_in_proj[primary_uid].emp_assigned_tasks.append(task_id)

        ltr_proj.proj_tasks[task_id] = ltr_task

    # ── Зависимости (parent → child) ─────────────────────────────────────────
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

    # ── Текущая нагрузка сотрудников ─────────────────────────────────────────
    for uid, emp in employees_in_proj.items():
        user_decl  = proj_declarations[proj_declarations['user_id'] == uid]
        total_hours = user_decl['duration'].sum()
        emp.emp_current_load = min(total_hours / proj_planned_days, 12.0)

    if len(ltr_proj.proj_dependencies) < MIN_PROJECT_DEPENDENCIES:
        continue

    all_projects[proj_id] = ltr_proj

    if len(all_projects) % 100 == 0:
        print(f"Обработано проектов: {len(all_projects)}")

print(f"Всего создано проектов: {len(all_projects)}")

# Диагностика: какие проекты из выборки потерялись и почему
built_ids   = set(all_projects.keys())
sampled_ids = set(sample_project_ids)
lost_ids    = sampled_ids - built_ids
if lost_ids:
    print(f"\nПотеряно проектов из выборки: {len(lost_ids)}")
    for pid in list(lost_ids)[:10]:
        proj_info = projects_full_sample[projects_full_sample['id'] == pid]
        n_tasks_raw   = len(tasks_full[tasks_full['project_id'] == pid])
        n_tasks_valid = len(tasks_full_sample[tasks_full_sample['project_id'] == pid])
        n_decl = len(declarations_sample[
            declarations_sample['task_id'].isin(
                tasks_full_sample[tasks_full_sample['project_id'] == pid]['id']
            )
        ])
        print(f"  {pid}: задач всего={n_tasks_raw}, "
              f"валидных={n_tasks_valid}, деклараций={n_decl}")

# ── Сохранение ────────────────────────────────────────────────────────────────
FILES_DIR.mkdir(parents=True, exist_ok=True)
output_file = FILES_DIR / "ltrroe_real_projects.pkl"
with open(output_file, "wb") as f:
    pickle.dump(all_projects, f)
print(f"Проекты сохранены в {output_file}")

# ── Sanity-check ──────────────────────────────────────────────────────────────
if all_projects:
    sample_pid  = next(iter(all_projects))
    sample_proj = all_projects[sample_pid]
    print(f"\nПример проекта {sample_pid}:")
    print(f"  Сотрудников:  {len(sample_proj.proj_employees)}")
    print(f"  Задач:        {len(sample_proj.proj_tasks)}")
    print(f"  Зависимостей: {len(sample_proj.proj_dependencies)}")
    print(f"  Начало:       {sample_proj.proj_start_date}")
