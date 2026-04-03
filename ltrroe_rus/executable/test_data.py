"""
Генератор тестовых данных для LTRROE
Создание полноценного тестового проекта для демонстрации и проверки системы
"""

from models import Employee, Task, Dependency, Project, Outsource
from datetime import datetime, timedelta

def create_test_project():
    """Создать полноценный тестовый проект (5 сотрудников, 10 задач)"""
    project = Project()
    project.proj_start_date = datetime(2026, 1, 3)  # Фиксированная дата начала
    
    # 1. СОЗДАЁМ 5 СОТРУДНИКОВ
    
    # 1 СЕНИОР - ведущий разработчик
    senior = Employee(
        emp_id=0,
        emp_name="Алексей Сеньоров",
        emp_skills=["архитектура", "Python", "ML", "DevOps"],
        emp_error_prob=0.10,
        emp_cost_per_hour=50.0,
        emp_efficiency={
            "архитектура": 1.3,
            "Python": 1.2,
            "ML": 1.2,
            "DevOps": 1.1
        }
    )
    
    # 2 МИДДЛ 1
    mid1 = Employee(
        emp_id=1,
        emp_name="Мария Миддлова",
        emp_skills=["Python", "UI/UX", "тестирование", "базы_данных"],
        emp_error_prob=0.15,
        emp_cost_per_hour=35.0,
        emp_efficiency={
            "Python": 1.0,
            "UI/UX": 1.1,
            "тестирование": 0.9,
            "базы_данных": 0.8
        }
    )
    
    # 3 МИДДЛ 2
    mid2 = Employee(
        emp_id=2,
        emp_name="Иван Миддлов",
        emp_skills=["DevOps", "Python", "базы_данных", "тестирование"],
        emp_error_prob=0.12,
        emp_cost_per_hour=32.0,
        emp_efficiency={
            "DevOps": 1.1,
            "Python": 0.9,
            "базы_данных": 1.0,
            "тестирование": 0.8
        }
    )
    
    # 4 ДЖУН 1
    junior1 = Employee(
        emp_id=3,
        emp_name="Ольга Джуниорова",
        emp_skills=["Python", "тестирование", "документация"],
        emp_error_prob=0.25,
        emp_cost_per_hour=20.0,
        emp_efficiency={
            "Python": 0.7,
            "тестирование": 0.8,
            "документация": 0.9
        }
    )
    
    # 5 ДЖУН 2
    junior2 = Employee(
        emp_id=4,
        emp_name="Дмитрий Джуниоров",
        emp_skills=["UI/UX", "документация", "Python"],
        emp_error_prob=0.30,
        emp_cost_per_hour=18.0,
        emp_efficiency={
            "UI/UX": 0.7,
            "документация": 1.0,
            "Python": 0.6
        }
    )
    
    # Добавляем сотрудников в проект
    employees = [senior, mid1, mid2, junior1, junior2]
    for emp in employees:
        project.proj_employees[emp.emp_id] = emp
    
    # 2. СОЗДАЁМ 10 ЗАДАЧ
    
    tasks = [
        Task(0, "Проектирование архитектуры системы", ["архитектура"], 5, 1000.0, (3, 5, 8)),
        Task(1, "Написание технической документации", ["документация"], 1, 200.0, (2, 3, 5)),
        Task(2, "Разработка ML модели", ["Python", "ML"], 4, 800.0, (7, 10, 14)),
        Task(3, "Реализация UI/UX дизайна", ["UI/UX", "Python"], 3, 600.0, (5, 7, 10)),
        Task(4, "Настройка DevOps инфраструктуры", ["DevOps", "Python"], 4, 700.0, (4, 6, 9)),
        Task(5, "Интеграция с внешним API", ["Python", "базы_данных"], 3, 500.0, (3, 4, 6)),
        Task(6, "Комплексное тестирование системы", ["тестирование", "Python"], 4, 400.0, (4, 5, 7)),
        Task(7, "Оптимизация производительности", ["архитектура", "Python"], 3, 600.0, (3, 4, 6)),
        Task(8, "Деплой на production", ["DevOps", "тестирование"], 5, 900.0, (2, 3, 5)),
        Task(9, "Финальная сборка и релиз", ["архитектура", "DevOps"], 5, 1000.0, (3, 4, 6))
    ]
    
    for task in tasks:
        project.proj_tasks[task.task_id] = task
    
    # 3. СОЗДАЁМ ЗАВИСИМОСТИ
    
    dependencies = [
        # Архитектура - основа для всего
        Dependency(0, 2, "FS", 0.0, True),  # Архитектура → ML
        Dependency(0, 3, "FS", 0.0, True),  # Архитектура → UI/UX
        Dependency(0, 4, "FS", 0.0, True),  # Архитектура → DevOps
        Dependency(0, 5, "FS", 0.0, True),  # Архитектура → API
        Dependency(0, 6, "FS", 0.0, True),  # Архитектура → Тестирование
        Dependency(0, 7, "FS", 0.0, True),  # Архитектура → Оптимизация
        Dependency(0, 8, "FS", 0.0, True),  # Архитектура → Деплой
        Dependency(0, 9, "FS", 0.0, True),  # Архитектура → Финальная
        
        # Дополнительные зависимости
        Dependency(2, 6, "FS", 2.0, True),   # ML → Тестирование (через 2 дня)
        Dependency(3, 6, "SS", 1.0, True),   # UI/UX → Тестирование (старт вместе)
        Dependency(4, 8, "FS", 1.0, True),   # DevOps → Деплой
        Dependency(6, 8, "FS", 0.0, True),   # Тестирование → Деплой
        Dependency(8, 9, "FS", 0.0, True),   # Деплой → Финальная
        
        # Документация может начаться в любое время
        Dependency(0, 1, "SS", 0.0, False),  # Архитектура → Документация (опционально)
    ]
    
    project.proj_dependencies = dependencies
    
    # 4. НАЗНАЧАЕМ ЗАДАЧИ
    
    # Задача 0: Архитектура → Senior (6ч/день)
    senior.emp_assigned_tasks.append(0)
    senior.emp_current_load += 6.0
    tasks[0].task_assigned_to.append(0)
    
    # Задача 1: Документация → Junior2 (4ч/день)
    junior2.emp_assigned_tasks.append(1)
    junior2.emp_current_load += 4.0
    tasks[1].task_assigned_to.append(4)
    
    # Задача 2: ML → Senior (4ч/день)
    senior.emp_assigned_tasks.append(2)
    senior.emp_current_load += 4.0
    tasks[2].task_assigned_to.append(0)
    
    # Задача 3: UI/UX → Junior2 (3ч) + Mid1 (3ч)
    junior2.emp_assigned_tasks.append(3)
    mid1.emp_assigned_tasks.append(3)
    junior2.emp_current_load += 3.0
    mid1.emp_current_load += 3.0
    tasks[3].task_assigned_to.extend([4, 1])
    
    # Задача 4: DevOps → Mid2 (5ч/день)
    mid2.emp_assigned_tasks.append(4)
    mid2.emp_current_load += 5.0
    tasks[4].task_assigned_to.append(2)
    
    # Задача 5: API → Mid1 (4ч/день)
    mid1.emp_assigned_tasks.append(5)
    mid1.emp_current_load += 4.0
    tasks[5].task_assigned_to.append(1)
    
    # Задача 6: Тестирование → Junior1 (4ч) + Mid1 (2ч)
    junior1.emp_assigned_tasks.append(6)
    mid1.emp_assigned_tasks.append(6)
    junior1.emp_current_load += 4.0
    mid1.emp_current_load += 2.0
    tasks[6].task_assigned_to.extend([3, 1])
    
    # Задача 7: Оптимизация → Senior (3ч/день)
    senior.emp_assigned_tasks.append(7)
    senior.emp_current_load += 3.0
    tasks[7].task_assigned_to.append(0)
    
    # Задача 8: Деплой → Mid2 (3ч) + Junior1 (3ч)
    mid2.emp_assigned_tasks.append(8)
    junior1.emp_assigned_tasks.append(8)
    mid2.emp_current_load += 3.0
    junior1.emp_current_load += 3.0
    tasks[8].task_assigned_to.extend([2, 3])
    
    # Задача 9: Финальная → Senior (4ч) + Mid2 (4ч)
    senior.emp_assigned_tasks.append(9)
    mid2.emp_assigned_tasks.append(9)
    senior.emp_current_load += 4.0
    mid2.emp_current_load += 4.0
    tasks[9].task_assigned_to.extend([0, 2])
    
    # 5. СОЗДАЁМ АУТСОРС-ВАРИАНТЫ
    
    project.proj_outsources = [
        Outsource(0, "Upwork DevOps Expert", ["DevOps", "Python", "базы_данных"], 
                  500.0, 0.8, 5, 1.3),
        Outsource(1, "Freelance UI/UX Designer", ["UI/UX", "Python"], 
                  400.0, 0.7, 3, 1.5)
    ]
    
    return project

def create_simple_project():
    """Создать минимальный проект для быстрого тестирования (3 задачи, 2 сотрудника)"""
    project = Project()
    project.proj_start_date = datetime(2026, 1, 1)
    
    # Простая команда
    alice = Employee(0, "Алиса", ["Python", "тестирование"], 0.1, 40.0, {"Python": 1.0, "тестирование": 0.9})
    bob = Employee(1, "Боб", ["DevOps", "Python"], 0.15, 35.0, {"DevOps": 1.1, "Python": 0.8})
    
    project.proj_employees = {0: alice, 1: bob}
    
    # Простые задачи
    tasks = [
        Task(0, "Проектирование", ["Python"], 3, 500.0, (2, 3, 5)),
        Task(1, "Реализация", ["Python", "DevOps"], 4, 800.0, (4, 5, 7)),
        Task(2, "Тестирование", ["тестирование"], 2, 300.0, (1, 2, 3))
    ]
    
    for task in tasks:
        project.proj_tasks[task.task_id] = task
    
    # Простые зависимости
    project.proj_dependencies = [
        Dependency(0, 1, "FS", 0.0, True),
        Dependency(1, 2, "FS", 1.0, True)
    ]
    
    # Назначения
    alice.emp_assigned_tasks = [0, 2]
    alice.emp_current_load = 5.0
    bob.emp_assigned_tasks = [1]
    bob.emp_current_load = 6.0
    
    tasks[0].task_assigned_to = [0]
    tasks[1].task_assigned_to = [1]
    tasks[2].task_assigned_to = [0]
    
    return project
