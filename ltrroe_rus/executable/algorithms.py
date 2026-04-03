"""
Ядро расчётов LTRROE - алгоритмы планирования и анализа рисков
Реализация forward/backward pass, симуляция Монте-Карло, учёт человеческого фактора
"""

from test_data import create_test_project
from datetime import timedelta, datetime
import random
from typing import Dict, List, Tuple

def get_predecessors(project, task_id: int) -> List[int]:
    """
    Найти всех предшественников задачи
    """
    preds = []
    for dep in project.proj_dependencies:
        if dep.dep_to_task == task_id:
            preds.append(dep.dep_from_task)
    return preds

def calculate_slowdown_factor(employee, task) -> float:
    """
    Рассчитать коэффициент замедления для сотрудника на задаче
    На основе несоответствия навыков и нагрузки
    """
    required_skills = task.task_skills
    employee_skills = employee.emp_skills

    # Проверка отсутствующих навыков
    missing_skills = [skill for skill in required_skills if skill not in employee_skills]
    missing_count = len(missing_skills)
    total_count = len(required_skills)

    # Если все навыки отсутствуют
    if missing_count == total_count:
        return 3.0  # Крайне медленно, не подходит для задачи

    # Если часть навыков отсутствует
    if missing_count > 0:
        missing_ratio = missing_count / total_count
        base_penalty = 2.0

        # Базовый 2.0 + дополнительный за каждый отсутствующий
        additional_penalty = missing_ratio * 1.0
        return base_penalty + additional_penalty
    
    # Находим минимальную эффективность по требуемым навыкам
    efficiencies = []
    for skill in required_skills:
        # Берём эффективность сотрудника по этому навыку, по умолчанию 0.20
        efficiency = employee.emp_efficiency.get(skill, 0.20)
        efficiencies.append(efficiency)
    
    min_efficiency = min(efficiencies)
    
    # Коэффициент от навыков
    skill_slowdown = 1.0 / min_efficiency
    
    # Коэффициент от перегрузки (если есть)
    overload_slowdown = 1.0
    if employee.emp_current_load > employee.emp_max_daily_hours:
        overload = employee.emp_current_load - employee.emp_max_daily_hours
        # +5% за каждый лишний час
        overload_slowdown = 1.0 + (overload * 0.05)
    
    # Общий коэффициент замедления
    total_slowdown = skill_slowdown * overload_slowdown
    
    return total_slowdown

def calculate_task_duration(task, project=None) -> float:
    """
    Рассчитать длительность задачи с учётом производительности исполнителя
    Использует формулу PERT для базовой оценки
    """
    # Базовая длительность (взвешенное среднее PERT)
    base_duration = (task.task_duration_dist[0] + task.task_duration_dist[1] * 4 + task.task_duration_dist[2]) / 6
    
    # Если нет проекта или нет назначений, возвращаем базовую длительность
    if project is None or not task.task_assigned_to:
        return base_duration
    
    # Безопасное получение основного исполнителя
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
    Выполнить forward pass для расчёта ранних дат начала и окончания
    Возвращает: early_start, early_finish, task_duration словари
    """
    early_start = {}  # task_id -> дата начала
    early_finish = {}  # task_id -> дата окончания
    task_duration = {}  # task_id -> длительность в днях
    
    # Рассчитать длительность для каждой задачи
    for task_id, task in project.proj_tasks.items():
        task_duration[task_id] = calculate_task_duration(task, project)
    
    # Обрабатываем задачи, пока все не обработаны
    processed = set()
    
    while len(processed) < len(project.proj_tasks):
        for task_id, task in project.proj_tasks.items():
            if task_id in processed:
                continue
            
            # Найти предшественников
            preds = get_predecessors(project, task_id)
            
            # Проверить можно ли обработать эту задачу?
            if not preds or all(p in processed for p in preds):
                # Определить дату начала
                if not preds:
                    # Нет зависимостей -> начинаем с начала проекта
                    start_date = project.proj_start_date
                else:
                    # Есть зависимости -> начинаем ПОСЛЕ окончания последнего предшественника
                    max_finish_date = max(early_finish[p] for p in preds)
                    start_date = max_finish_date
                
                # Рассчитать дату окончания
                duration_days = task_duration[task_id]
                finish_date = start_date + timedelta(days=duration_days)
                
                # Сохранить результаты
                early_start[task_id] = start_date
                early_finish[task_id] = finish_date
                processed.add(task_id)
    
    return early_start, early_finish, task_duration

def get_successors(project, task_id: int) -> List[int]:
    """
    Найти всех последователей задачи
    """
    successors = []
    for dep in project.proj_dependencies:
        if dep.dep_from_task == task_id:
            successors.append(dep.dep_to_task)
    return successors

def calculate_backward_pass(project, early_finish: Dict, task_duration: Dict) -> Tuple[Dict, Dict]:
    """
    Выполнить backward pass для расчёта поздних дат начала и окончания
    Возвращает: late_start, late_finish словари
    """
    late_start = {}
    late_finish = {}
    
    # Крайний срок проекта (условно, без буфера)
    project_deadline = max(early_finish.values())
    
    # Инициализировать поздние даты окончания для конечных задач
    for task_id in project.proj_tasks.keys():
        succs = get_successors(project, task_id)
        if not succs:
            late_finish[task_id] = project_deadline
    
    # обрабатываем задачи в порядке убывания early_finish
    tasks_sorted = sorted(project.proj_tasks.items(), 
                         key=lambda x: early_finish[x[0]], 
                         reverse=True)
    
    for task_id, task in tasks_sorted:
        succs = get_successors(project, task_id)
        
        if succs:
            # Найти минимальный поздний старт среди последователей
            min_late_start = min(late_start.get(s, project_deadline) for s in succs)
            late_finish[task_id] = min_late_start
        
        # Рассчитать поздний старт
        late_start[task_id] = late_finish[task_id] - timedelta(days=task_duration[task_id])
    
    return late_start, late_finish

def random_triangular(low: float, most_likely: float, high: float) -> float:
    """
    Генерация случайного числа из треугольного распределения
    Используется для симуляции PERT
    """
    u = random.random()
    
    if u == 0:
        return low
    elif u == 1:
        return high
    
    # Нормализуем most_likely
    c = (most_likely - low) / (high - low)
    
    if u < c:
        return low + (u * (high - low) * (most_likely - low)) ** 0.5
    else:
        return high - ((1 - u) * (high - low) * (high - most_likely)) ** 0.5

def forward_pass_with_random_duration(project, random_duration: Dict) -> Dict:
    """
    Выполнить forward pass со стохастическими длительностями задач
    Возвращает: early_finish словарь для одной симуляции
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
    Симуляция Монте-Карло для оценки рисков проекта
    Возвращает: Список длительностей проекта из всех симуляций
    """
    project_durations = []
    
    for sim in range(num_simulations):
        random_durations = {}
        
        for task_id, task in project.proj_tasks.items():
            # Генерируем базовую случайную длительность
            low, most_likely, high = task.task_duration_dist
            base_random = random_triangular(low, most_likely, high)
            
            # Корректировка с учётом производительности исполнителя
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
        
        # Выполняем forward pass со случайными длительностями
        early_finish = forward_pass_with_random_duration(project, random_durations)
        
        if early_finish:
            max_finish_date = max(early_finish.values())
            project_duration = (max_finish_date - project.proj_start_date).days
            project_durations.append(project_duration)
    
    return project_durations
