"""
Модели данных системы LTRROE
Определение основных классов и структур для представления сущностей проекта
Используется в рамках исследовательского прототипа для обеспечения
типизации и структурированного хранения информации

Основные классы:
- Задача: задача проекта с атрибутами длительности, критичности, требуемых навыков
- Сотрудник: сотрудник с характеристиками компетенций, загрузки, вероятности ошибок
- Проект: контейнер проекта, объединяющий задачи, сотрудников и зависимости
- Зависимость: зависимость между задачами с типом и временной задержкой
- Аутсорс: вариант аутсорсинга задачи
- Назначение: назначение задачи на сотрудника

Архитектура:
Классы реализованы с методами для удобной работы и расчёта производных параметров.
Каждый класс содержит все необходимые атрибуты для моделирования и анализа.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional

class Employee:
    def __init__(self, emp_id: int, emp_name: str, emp_skills: List[str],
                 emp_error_prob: float, emp_cost_per_hour: float,
                 emp_efficiency: Dict[str, float]):
        self.emp_id = emp_id
        self.emp_name = emp_name
        self.emp_skills = emp_skills  # Список навыков сотрудника
        self.emp_error_prob = emp_error_prob 
        self.emp_cost_per_hour = emp_cost_per_hour
        self.emp_efficiency = emp_efficiency  # Эффективность по навыкам (0.6 = 60%, 1.2 = 120% от нормы)
        self.emp_max_daily_hours = 8.0
        self.emp_current_load = 0.0
        self.emp_fatigue = 1.0  # Множитель усталости: >1 = устал, <1 = отдохнул
        self.emp_assigned_tasks = []  # Назначенные задачи

class Task:
    def __init__(self, task_id: int, task_name: str, task_skills: List[str], 
                 task_crit: int, task_cost: float, task_duration_dist: tuple):
        self.task_id = task_id
        self.task_name = task_name
        self.task_skills = task_skills  # Требуемые навыки для задачи
        self.task_crit = task_crit  # Критичность задачи (1-5), 5 = самая важная
        self.task_cost = task_cost
        self.task_duration_dist = task_duration_dist
        self.task_assigned_to = []  # Кому назначена задача
        self.task_status = "in_progress"  # Текущий статус задачи
        self.task_actual_duration = None
        self.task_primary_assignee = None 

class Dependency:
    def __init__(self, dep_from_task: int, dep_to_task: int, 
                 dep_type: str, dep_lag: float, dep_mandatory: bool = True):
        self.dep_from_task = dep_from_task  # Предшествующая задача
        self.dep_to_task = dep_to_task  # Последующая задача
        self.dep_type = dep_type  # "FS", "SS", "FF", "SF"
        self.dep_lag = dep_lag  # Задержка в днях
        self.dep_mandatory = dep_mandatory

class Outsource:
    def __init__(self, outs_id: int, outs_name: str, outs_skills: List[str],
                 outs_daily_cost: float, outs_reliability: float,
                 outs_lead_time_days: int, outs_duration_multiplier: float = 1.5):
        self.outs_id = outs_id
        self.outs_name = outs_name
        self.outs_skills = outs_skills  # Навыки аутсорс-работника
        self.outs_daily_cost = outs_daily_cost
        self.outs_reliability = outs_reliability  # Надёжность (эффективность) работника
        self.outs_lead_time_days = outs_lead_time_days  # Задержка на подключение
        self.outs_duration_multiplier = outs_duration_multiplier  # Коэффициент длительности (>1)

class Project:
    def __init__(self):
        self.proj_employees: Dict[int, Employee] = {}  # Словарь сотрудников
        self.proj_tasks: Dict[int, Task] = {}  # Словарь задач
        self.proj_dependencies: List[Dependency] = []  # Список зависимостей
        self.proj_outsources: List[Outsource] = []  # Список аутсорс-опций
        self.proj_start_date = datetime.now()  # Дата начала проекта
        self.proj_current_date = datetime.now()  # Текущая дата в симуляции
        self.proj_simulation_results = {}  # Результаты симуляций Монте-Карло
