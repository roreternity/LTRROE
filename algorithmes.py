"""
Ядро расчётов LTRROE - алгоритмы планирования и анализа рисков
Реализация forward/backward pass, симуляция Монте-Карло, учёт человеческого фактора
"""

from test_data import create_test_project
from datetime import timedelta, datetime
import random

def get_predecessors(project, task_id):
    """
    Найти всех предшественников задачи
    """
    preds = []
    for dep in project.proj_dependencies:
        if dep.dep_to_task == task_id:
            preds.append(dep.dep_from_task)
    return preds

def calculate_slowdown_factor(employee, task):
    """
    Рассчитать коэффициент медлительности для сотрудника на задаче
    """
    # Проверяем, знает ли сотрудник все требуемые навыки
    required_skills = task.task_skills
    employee_skills = employee.emp_skills

    # Проверяем отсутствующие навыки
    missing_skills = [skill for skill in required_skills if skill not in employee_skills]
    missing_count = len(missing_skills)
    total_count = len(required_skills)

    # Если все навыки отсутствуют
    if missing_count == total_count:
        return 3.0 # крайне медленно, не подходит для задачи

    # Если часть навыков отсутствует
    if missing_count > 0:
        missing_ratio = missing_count / total_count
        base_penalty = 2.0

        # Базовый 2.0 + дополнительный за каждый отсутствующий
        additional_penalty = missing_ration * 1.0
        return base_penalty + additional_penalty
    
    # Находим минимальную эффективность по требуемым навыкам
    efficiencies = []
    for skill in required_skills:
        # Берём эффективность сотрудника по этому навыку
        # Если навыка нет в emp_efficiency, используем 0.20 (плохо)
        efficiency = employee.emp_efficiency.get(skill, 0.20)
        efficiencies.append(efficiency)
    
    min_efficiency = min(efficiencies)
    
    # Коэффициент от навыков
    skill_slowdown = 1.0 / min_efficiency
    
    # Коэффициент от перегрузки (если есть)
    overload_slowdown = 1.0
    if employee.emp_current_load > employee.emp_max_daily_hours:
        overload = employee.emp_current_load - employee.emp_max_daily_hours
        # +10% за каждый лишний час
        overload_slowdown = 1.0 + (overload * 0.05)
    
    # Общий коэффициент
    total_slowdown = skill_slowdown * overload_slowdown
    
    return total_slowdown
        
    
def calculate_task_duration(task, project=None):
    """
    Рассчитать длительность задачи с учетом исполнителя
    """
    # Базовая длительность (средняя по PERT)
    base_duration = (task.task_duration_dist[0] + 
                     task.task_duration_dist[1] * 4 + 
                     task.task_duration_dist[2]) / 6
    
    # Если нет проекта или нет назначений
    if project is None or not task.task_assigned_to:
        return base_duration
    
    # Безопасное получение исполнителя
    try:
        primary_emp_id = task.task_assigned_to[0]
        employee = project.proj_employees.get(primary_emp_id)
        
        if employee is None:
            return base_duration
            
        slowdown = calculate_slowdown_factor(employee, task)
        return base_duration * slowdown
        
    except (IndexError, KeyError):
        return base_duration
    
def calculate_schedule(project):
    """
    Рассчитать ранние даты начала и окончания задач
    """
    early_start = {}  # task_id - дата начала
    early_finish = {}  # task_id - дата окончания
    task_duration = {}  # task_id - длительность (дней)
    
    # Рассчитать длительность каждой задачи
    for task_id, task in project.proj_tasks.items():
        task_duration[task_id] = calculate_task_duration(task, project)
    
    # Обрабатываем задачи, пока все не обработаны
    processed = set()  # какие задачи уже обработаны
    
    while len(processed) < len(project.proj_tasks):
        for task_id, task in project.proj_tasks.items():
            if task_id in processed:
                continue  # уже обработали
            
            # Найти предшественников
            preds = get_predecessors(project, task_id)
            
            # Проверить можно ли обработать эту задачу?
            # Либо нет предшественников, либо все предшественники уже обработаны
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
                processed.add(task_id)  # пометить как обработанную
    
    return early_start, early_finish, task_duration

def get_successors(project, task_id):
    """
    Найти всех потомков задачи
    """
    sces = []
    for dep in project.proj_dependencies:
        if dep.dep_from_task == task_id:
            sces.append(dep.dep_to_task)
    return sces

def calculate_backward_pass(project, early_finish, task_duration):
    """
    Рассчитать поздние даты начала и окончания
    """
    late_start = {}
    late_finish = {}
    
    # Находим крайний срок проекта
    project_deadline = max(early_finish.values())
    
    # Инициализируем поздние даты окончания для конечных задач
    for task_id in project.proj_tasks.keys():
        succs = get_successors(project, task_id)
        if not succs:
            late_finish[task_id] = project_deadline
    
    # обрабатываем задачи в порядке убывания early_finish
    tasks_sorted = sorted(project.proj_tasks.items(), key=lambda x: early_finish[x[0]], reverse=True)
    
    for task_id, task in tasks_sorted:
        succs = get_successors(project, task_id)
        
        if succs:
            # Находим минимальный поздний старт среди последователей
            min_late_start = min(late_start.get(s, project_deadline) for s in succs)
            late_finish[task_id] = min_late_start
        # Если нет последователей, уже установили project_deadline выше
        # Рассчитываем поздний старт
        late_start[task_id] = late_finish[task_id] - timedelta(days=task_duration[task_id])
    
    return late_start, late_finish

def random_triangular(low, most_likely, high):
    """
    Генерация случайного числа из треугольного распределения.
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

def forward_pass_with_random_duration(project, random_duration):
    """
    Рассчитать ранние даты начала и окончания задач
    """
    early_start = {}  # task_id - дата начала
    early_finish = {}  # task_id - дата окончания
    processed = set()  # какие задачи уже обработаны
    
    while len(processed) < len(project.proj_tasks):
        for task_id, task in project.proj_tasks.items():
            if task_id in processed:
                continue  # обработали
            
            # Найти предшественников
            preds = get_predecessors(project, task_id)
            
            # Проверить: можно ли обработать эту задачу?
            # Либо нет предшественников, либо все предшественники уже обработаны
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
                duration_days = random_duration[task_id]
                finish_date = start_date + timedelta(days=duration_days)
                
                # Сохранить результаты
                early_start[task_id] = start_date
                early_finish[task_id] = finish_date
                processed.add(task_id)  # отметить как обработанную
    return early_finish

def monte_carlo_simulation(project, num_simulations=1000):
    """
    Базовая симуляция Монте-Карло с учетом медлительности
    """
    project_durations = []  # сюда будем складывать длительности проекта
    
    for sim in range(num_simulations):
        random_durations = {}  # словарь task_id - случайная длительность
        
        for task_id, task in project.proj_tasks.items():
            # Генерируем базовую случайную длительность
            low, most_likely, high = task.task_duration_dist
            base_random = random_triangular(low, most_likely, high)
            # Корректировка с учётом медлительности исполнителя
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
            # Находим максимальную дату окончания (длительность проекта)
            max_finish_date = max(early_finish.values())
            project_duration = (max_finish_date - project.proj_start_date).days
            project_durations.append(project_duration)
    
    return project_durations

if __name__ == "__main__":
    print("Тестируем создание проекта...")
    project = create_test_project()
    
    # Детерминированный расчет
    early_start, early_finish, task_duration = calculate_schedule(project)

    # Backward pass
    late_start, late_finish = calculate_backward_pass(project, early_finish, task_duration)
    
    print("\nBACKWARD PASS РЕЗУЛЬТАТЫ:")
    for task_id in sorted(late_start.keys()):
        print(f"\nЗадача {task_id}:")
        print(f"  Поздний старт: {late_start[task_id].strftime('%d.%m.%Y')}")
        print(f"  Позднее окончание: {late_finish[task_id].strftime('%d.%m.%Y')}")
        
        # Slack расчёт
        slack_days = (late_start[task_id] - early_start[task_id]).days
        print(f"  Slack (запас): {slack_days} дней")
        if slack_days == 0:
            print(f"  ⚠️ КРИТИЧЕСКАЯ ЗАДАЧА!")

    print("\nРЕЗУЛЬТАТЫ РАСЧЁТА РАСПИСАНИЯ:")
    for task_id in sorted(early_start.keys()):
        start = early_start[task_id].strftime("%d.%m.%Y")
        finish = early_finish[task_id].strftime("%d.%m.%Y")
        duration = (early_finish[task_id] - early_start[task_id]).days
        
        print(f"\nЗадача {task_id}:")
        print(f"  Начинается: {start}")
        print(f"  Заканчивается: {finish}")
        print(f"  Длительность: {duration} дней")
        
        # Показать зависимости
        preds = get_predecessors(project, task_id)
        if preds:
            print(f"  Зависит от задач: {preds}")

    # Тест random_triangular
    print("\nТест random_triangular:")
    test_values = []
    for _ in range(1000):
        val = random_triangular(14, 21, 28)
        test_values.append(val)
    
    print(f"  Сгенерировано {len(test_values)} значений")
    print(f"  Среднее: {sum(test_values)/len(test_values):.2f}")
    print(f"  Мин: {min(test_values):.2f}, Макс: {max(test_values):.2f}")

    # Быстрый тест Монте-Карло с зависимостями
    print("\nТест Монте-Карло с зависимостями:")
    durations_with_deps = monte_carlo_simulation(project, num_simulations=100)

    if durations_with_deps:
        print(f"  Симуляций: {len(durations_with_deps)}")
        print(f"  Среднее: {sum(durations_with_deps)/len(durations_with_deps):.1f} дней")
        print(f"  Мин: {min(durations_with_deps):.1f} дней, Макс: {max(durations_with_deps):.1f} дней")
        
        # Сравним с детерминированным расчётом
        print(f"\nСравнение:")
        project_end_date = max(early_finish.values())
        deterministic_duration = (project_end_date - project.proj_start_date).days
        print(f"  Детерминированно: {deterministic_duration} дней")
        print(f"  Монте-Карло (среднее): {sum(durations_with_deps)/len(durations_with_deps):.1f} дней")
        
        # Риски
        deadline = 30
        success = sum(1 for d in durations_with_deps if d <= deadline)
        success_rate = (success/len(durations_with_deps)*100) if durations_with_deps else 0
        print(f"  Риск срыва ({deadline} дней): {100 - success_rate:.1f}%")
    else:
        print("  ❌ Ошибка: durations_with_deps пустой")
