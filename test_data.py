"""
Модели для тестового запуска, проверка системы на работоспособность и корректность результатов
"""

from models import Employee, Task, Dependency, Project, Outsource, Assignment
from datetime import datetime, timedelta
import random

def create_test_project():
    """Создаем полноценный тестовый проект (5 сотрудников, 10 задач)"""
    project = Project()
    project.proj_start_date = datetime(2026, 1, 3)  # 03.01.2026
    
    # 1. СОЗДАЁМ 5 СОТРУДНИКОВ
    
    # 1 СЕНИОР - "звезда команды"
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
    
    # 2 МИДДЛ 1 (миддл)
    mid1 = Employee(
        emp_id=1,
        emp_name="Мария Миддлова",
        emp_skills=["Python", "UI/UX", "тестирование", "базы данных"],
        emp_error_prob=0.15,
        emp_cost_per_hour=35.0,
        emp_efficiency={
            "Python": 1.0,
            "UI/UX": 1.1,
            "тестирование": 0.9,
            "базы данных": 0.8
        }
    )
    
    # 3 МИДДЛ 2 (миддл)
    mid2 = Employee(
        emp_id=2,
        emp_name="Иван Миддлов",
        emp_skills=["DevOps", "Python", "базы данных", "тестирование"],
        emp_error_prob=0.12,
        emp_cost_per_hour=32.0,
        emp_efficiency={
            "DevOps": 1.1,
            "Python": 0.9,
            "базы данных": 1.0,
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
    
    #  2. СОЗДАЁМ 10 ЗАДАЧ 
    
    # СОЛО задачи (требуют один навык)
    # Задача 0: Проектирование архитектуры (только архитектура)
    task0 = Task(
        task_id=0,
        task_name="Проектирование архитектуры",
        task_skills=["архитектура"],
        task_crit=5,  # самая критичная
        task_cost=1000.0,
        task_duration_dist=(3, 5, 8)  # (оптимальная, вероятная, пессимистичная)
    )
    
    # Задача 1: Написание документации (только документация)
    task1 = Task(
        task_id=1,
        task_name="Написание документации",
        task_skills=["документация"],
        task_crit=1,  # наименее критичная
        task_cost=200.0,
        task_duration_dist=(2, 3, 5)
    )
    
    # "ПАРНЫЕ" задачи (требуют комбинацию навыков)
    # Задача 2: Разработка ML модели (Python + ML)
    task2 = Task(
        task_id=2,
        task_name="Разработка ML модели",
        task_skills=["Python", "ML"],
        task_crit=4,
        task_cost=800.0,
        task_duration_dist=(7, 10, 14)
    )
    
    # Задача 3: Создание UI/UX (UI/UX + Python)
    task3 = Task(
        task_id=3,
        task_name="Создание UI/UX дизайна",
        task_skills=["UI/UX", "Python"],
        task_crit=3,
        task_cost=600.0,
        task_duration_dist=(5, 7, 10)
    )
    
    # Задача 4: Настройка DevOps (DevOps + Python)
    task4 = Task(
        task_id=4,
        task_name="Настройка DevOps инфраструктуры",
        task_skills=["DevOps", "Python"],
        task_crit=4,
        task_cost=700.0,
        task_duration_dist=(4, 6, 9)
    )
    
    # Задача 5: Интеграция с API (Python + базы данных)
    task5 = Task(
        task_id=5,
        task_name="Интеграция с внешним API",
        task_skills=["Python", "базы данных"],
        task_crit=3,
        task_cost=500.0,
        task_duration_dist=(3, 4, 6)
    )
    
    # Задача 6: Тестирование системы (тестирование + Python)
    task6 = Task(
        task_id=6,
        task_name="Комплексное тестирование системы",
        task_skills=["тестирование", "Python"],
        task_crit=4,
        task_cost=400.0,
        task_duration_dist=(4, 5, 7)
    )
    
    # Задача 7: Оптимизация производительности (архитектура + Python)
    task7 = Task(
        task_id=7,
        task_name="Оптимизация производительности",
        task_skills=["архитектура", "Python"],
        task_crit=3,
        task_cost=600.0,
        task_duration_dist=(3, 4, 6)
    )
    
    # Задача 8: Деплой на production (DevOps + тестирование)
    task8 = Task(
        task_id=8,
        task_name="Деплой на production",
        task_skills=["DevOps", "тестирование"],
        task_crit=5,
        task_cost=900.0,
        task_duration_dist=(2, 3, 5)
    )
    
    # Задача 9: Финальная сборка (архитектура + DevOps)
    task9 = Task(
        task_id=9,
        task_name="Финальная сборка и релиз",
        task_skills=["архитектура", "DevOps"],
        task_crit=5,
        task_cost=1000.0,
        task_duration_dist=(3, 4, 6)
    )
    
    # Добавляем задачи в проект
    tasks = [task0, task1, task2, task3, task4, task5, task6, task7, task8, task9]
    for task in tasks:
        project.proj_tasks[task.task_id] = task
    
    # 3. СОЗДАЁМ ЗАВИСИМОСТИ
    
    # Базовые зависимости: все задачи зависят от архитектуры (task0)
    for task_id in [2, 3, 4, 5, 6, 7, 8, 9]:
        dep = Dependency(
            dep_from_task=0,  # архитектура
            dep_to_task=task_id,
            dep_type="FS",  # Finish-Start
            dep_lag=0.0,
            dep_mandatory=True
        )
        project.proj_dependencies.append(dep)
    
    # Дополнительные зависимости:
    # ML модель (task2) → Тестирование (task6)
    project.proj_dependencies.append(Dependency(2, 6, "FS", 0.0, True))
    
    # UI/UX (task3) → Тестирование (task6)  
    project.proj_dependencies.append(Dependency(3, 6, "SS", 2.0, True))  # Start-Start с лагом
    
    # DevOps (task4) → Деплой (task8)
    project.proj_dependencies.append(Dependency(4, 8, "FS", 1.0, True))
    
    # Тестирование (task6) → Деплой (task8)
    project.proj_dependencies.append(Dependency(6, 8, "FS", 0.0, True))
    
    # Деплой (task8) → Финальная сборка (task9)
    project.proj_dependencies.append(Dependency(8, 9, "FS", 0.0, True))
    
    # ========== 4. НАЗНАЧАЕМ ЗАДАЧИ ==========
    
    # Простая логика назначения (можно потом улучшить):
    # Задача 0 (архитектура) → Сеньор
    task0.task_assigned_to.append(0)
    senior.emp_assigned_tasks.append(0)
    senior.emp_current_load += 6.0
    
    # Задача 1 (документация) → Джун 2
    task1.task_assigned_to.append(4)
    junior2.emp_assigned_tasks.append(1)
    junior2.emp_current_load += 4.0
    
    # Задача 2 (ML модель) → Сеньор
    task2.task_assigned_to.append(0)
    senior.emp_assigned_tasks.append(2)
    senior.emp_current_load += 4.0
    
    # Задача 3 (UI/UX) → Джун 2 + Миддл 1
    task3.task_assigned_to.append(4)  # UI/UX часть
    task3.task_assigned_to.append(1)  # Python часть
    junior2.emp_assigned_tasks.append(3)
    mid1.emp_assigned_tasks.append(3)
    junior2.emp_current_load += 3.0
    mid1.emp_current_load += 3.0
    
    # Задача 4 (DevOps) → Миддл 2
    task4.task_assigned_to.append(2)
    mid2.emp_assigned_tasks.append(4)
    mid2.emp_current_load += 5.0
    
    # Задача 5 (API интеграция) → Миддл 1
    task5.task_assigned_to.append(1)
    mid1.emp_assigned_tasks.append(5)
    mid1.emp_current_load += 4.0
    
    # Задача 6 (Тестирование) → Джун 1 + Миддл 1
    task6.task_assigned_to.append(3)
    task6.task_assigned_to.append(1)
    junior1.emp_assigned_tasks.append(6)
    mid1.emp_assigned_tasks.append(6)
    junior1.emp_current_load += 4.0
    mid1.emp_current_load += 2.0
    
    # Задача 7 (Оптимизация) → Сеньор
    task7.task_assigned_to.append(0)
    senior.emp_assigned_tasks.append(7)
    senior.emp_current_load += 3.0
    
    # Задача 8 (Деплой) → Миддл 2 + Джун 1
    task8.task_assigned_to.append(2)
    task8.task_assigned_to.append(3)
    mid2.emp_assigned_tasks.append(8)
    junior1.emp_assigned_tasks.append(8)
    mid2.emp_current_load += 3.0
    junior1.emp_current_load += 3.0
    
    # Задача 9 (Финальная сборка) → Сеньор + Миддл 2
    task9.task_assigned_to.append(0)
    task9.task_assigned_to.append(2)
    senior.emp_assigned_tasks.append(9)
    mid2.emp_assigned_tasks.append(9)
    senior.emp_current_load += 4.0
    mid2.emp_current_load += 4.0
    
    # ========== 5. СОЗДАЁМ АУТСОРСОВ ==========
    
    outs1 = Outsource(
        outs_id=0,
        outs_name="Upwork DevOps Expert",
        outs_skills=["DevOps", "Python", "базы данных"],
        outs_daily_cost=500.0,
        outs_reliability=0.8,
        outs_lead_time_days=5,
        outs_duration_multiplier=1.3
    )
    
    outs2 = Outsource(
        outs_id=1,
        outs_name="Freelance UI/UX Designer",
        outs_skills=["UI/UX", "Python"],
        outs_daily_cost=400.0,
        outs_reliability=0.7,
        outs_lead_time_days=3,
        outs_duration_multiplier=1.5
    )
    
    project.proj_outsources.append(outs1)
    project.proj_outsources.append(outs2)
    
    return project

# ТЕСТИРУЕМ
if __name__ == "__main__":
    print("Тестируем создание полноценного проекта...")
    print("="*60)
    
    project = create_test_project()
    
    print(f"✅ СОЗДАНО:")
    print(f"   Сотрудников: {len(project.proj_employees)}")
    print(f"   Задач: {len(project.proj_tasks)}")
    print(f"   Зависимостей: {len(project.proj_dependencies)}")
    print(f"   Аутсорсов: {len(project.proj_outsources)}")
    
    print("\n👥 СОТРУДНИКИ:")
    for emp_id, emp in sorted(project.proj_employees.items()):
        print(f"  {emp.emp_name} (ID:{emp_id}):")
        print(f"    Навыки: {emp.emp_skills}")
        print(f"    Загрузка: {emp.emp_current_load:.1f} часов/день")
        print(f"    Задачи: {emp.emp_assigned_tasks}")
    
    print("\n📋 ЗАДАЧИ:")
    for task_id, task in sorted(project.proj_tasks.items()):
        print(f"  {task_id}. {task.task_name}:")
        print(f"     Навыки: {task.task_skills}")
        print(f"     Критичность: {task.task_crit}")
        print(f"     Назначена на: {task.task_assigned_to}")
        print(f"     Длительность: {task.task_duration_dist}")
    
    print("\n🔗 ЗАВИСИМОСТИ (первые 5):")
    for i, dep in enumerate(project.proj_dependencies[:5]):
        print(f"  {dep.dep_from_task} → {dep.dep_to_task} ({dep.dep_type})")
