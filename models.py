"""
Модели данных системы LTRROE
Определяет основные классы и структуры для представления сущностей проекта
Используется в рамках исследовательского прототипа для обеспечения
типизации и структурированного хранения информации

Основные классы:
- Task: задача проекта с атрибутами длительности, критичности, требуемых навыков
- Employee: сотрудник с характеристиками компетенций, загрузки, вероятности ошибок
- Project: контейнер проекта, объединяющий задачи, сотрудников и зависимости
- Dependency: зависимость между задачами с типом и лагом
- Outsource: вариант аутсорсинга задачи
- Assignment: назначение задачи на сотрудника

Архитектура:
Классы реализованы с методами для удобной работы и расчета производных параметров.
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
        self.emp_skills = emp_skills # список навыков сотрудника
        self.emp_error_prob = emp_error_prob 
        self.emp_cost_per_hour = emp_cost_per_hour
        self.emp_efficiency = emp_efficiency # эффективность по навыкам (0.6 = 60%, 1.2 = 120% от нормы)
        self.emp_max_daily_hours = 8.0
        self.emp_current_load = 0.0
        self.emp_fatigue = 1.0 # множитель усталости: >1 = устал, <1 = отдохнул (влияет на ошибки и скорость)
        self.emp_assigned_tasks = [] # назначенные задачи

class Task:
    def __init__(self, task_id: int, task_name: str, task_skills: List[str], 
                 task_crit: int, task_cost: float, task_duration_dist: tuple):
        self.task_id = task_id
        self.task_name = task_name
        self.task_skills = task_skills # список требуемых навыков для задачи
        self.task_crit = task_crit # критичность задачи (1-5), где 5 = самая важная, влияет на приоритет
        self.task_cost = task_cost
        self.task_duration_dist = task_duration_dist
        self.task_assigned_to = [] # кому назначена задача
        self.task_status = "pending" # текущий статус задачи
        self.task_actual_duration = None
        self.task_primary_assignee = None 

class Dependency:
    def __init__(self, dep_from_task: int, dep_to_task: int, 
                 dep_type: str, dep_lag: float, dep_mandatory: bool = True):
        self.dep_from_task = dep_from_task # зависит ли ее начало от конца другой задачи
        self.dep_to_task = dep_to_task # зависит ли от ее конца начало другой задачи
        self.dep_type = dep_type  # "FS", "SS", "FF", "SF"
        self.dep_lag = dep_lag # какая задержка в днях после задачи
        self.dep_mandatory = dep_mandatory

class Outsource:
    def __init__(self, outs_id: int, outs_name: str, outs_skills: List[str],
                 outs_daily_cost: float, outs_reliability: float,
                 outs_lead_time_days: int, outs_duration_multiplier: float = 1.5):
        self.outs_id = outs_id
        self.outs_name = outs_name
        self.outs_skills = outs_skills # навыки аутсорс-работника
        self.outs_daily_cost = outs_daily_cost
        self.outs_reliability = outs_reliability # надежность (эффективность) работника в целом
        self.outs_lead_time_days = outs_lead_time_days # задержка на подключение к проекту
        self.outs_duration_multiplier = outs_duration_multiplier # коэффицент длительности выполнения задач конкретно аутсорсом (>1)

class Project:
    def __init__(self):
        self.proj_employees: Dict[int, Employee] = {} # словарь работников
        self.proj_tasks: Dict[int, Task] = {} # словарь задач (для учета зависимостей и точных сроков выполнения проекта)
        self.proj_dependencies: List[Dependency] = [] # список зависимостей (полный учет зависимостей)
        self.proj_outsources: List[Outsource] = [] # список аутсорс-опций для проекта
        self.proj_start_date = datetime.now() # дата начала проекта
        self.proj_current_date = datetime.now() # текущая дата в симуляции (для "что если" анализа)
        self.proj_simulation_results = {} # здесь сохраняются результаты симуляций Монте-Карло

class Assignment:
    def __init__(self, asg_task_id: int, asg_emp_id: int, 
                 asg_planned_start: datetime, asg_planned_end: datetime,
                 asg_hours_per_day: float):
        self.asg_task_id = asg_task_id # список назначенных задач
        self.asg_emp_id = asg_emp_id # список тех кто назначен на задачи
        self.asg_planned_start = asg_planned_start # планируемая дата назначения (и старта работы)
        self.asg_planned_end = asg_planned_end # планируемся дата снятия с задачи (конец работы над задачей)
        self.asg_hours_per_day = asg_hours_per_day # сколько работы выполняется по назначенной задаче в часах
        self.asg_actual_start = None
        self.asg_actual_end = None
        self.asg_progress = 0.0 # прогресс от старта назначения на задачу
