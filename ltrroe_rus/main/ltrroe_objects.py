"""
Модели данных системы LTRROE
Определяет основные классы и структуры для представления сущностей проекта
Используется в исследовательском прототипе для обеспечения типизации и структурированного хранения данных

Основные классы:
- Task: Задача проекта с атрибутами длительности, критичности, требуемых навыков
- Employee: Сотрудник с характеристиками компетенций, загрузки, вероятности ошибок
- Project: Контейнер проекта, объединяющий задачи, сотрудников и зависимости
- Dependency: Связь между задачами с типом и временным лагом
- Outsource: Опция аутсорсинга задачи
- Assignment: Назначение задачи сотруднику

Архитектура:
Классы реализованы с методами для удобных операций и расчёта производных параметров.
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
        self.emp_efficiency = emp_efficiency  # Эффективность по навыку (0.6 = 60%, 1.2 = 120% от базового уровня)
        self.emp_max_daily_hours = 8.0
        self.emp_current_load = 0.0
        self.emp_fatigue = 1.0  # Множитель усталости: >1 = устал, <1 = отдохнул (влияет на ошибки и скорость)
        self.emp_assigned_tasks = []  # Текущие назначенные задачи

class Task:
    def __init__(self, task_id: int, task_name: str, task_skills: List[str], 
                 task_crit: int, task_cost: float, task_duration_dist: tuple):
        self.task_id = task_id
        self.task_name = task_name
        self.task_skills = task_skills  # Требуемые навыки для задачи
        self.task_crit = task_crit  # Критичность задачи (1-5), 5 = наивысший приоритет
        self.task_cost = task_cost
        self.task_duration_dist = task_duration_dist
        self.task_assigned_to = []  # Назначенные сотрудники
        self.task_status = "in_progress"  # Текущий статус; допустимые статусы: ['not_started', 'in_progress', 'completed', 'blocked']
        self.task_actual_duration = None
        self.task_primary_assignee = None 

class Dependency:
    def __init__(self, dep_from_task: int, dep_to_task: int, 
                 dep_type: str, dep_lag: float, 
                 dep_mandatory: bool = True, dep_id: Optional[int] = None):
        self.dep_id = dep_id
        self.dep_from_task = dep_from_task  # Задача-предшественник
        self.dep_to_task = dep_to_task  # Задача-последователь
        self.dep_type = dep_type  # "FS", "SS", "FF", "SF"
        self.dep_lag = dep_lag  # Лаг в днях
        self.dep_mandatory = dep_mandatory

class Outsource:
    def __init__(self, outs_id: int, outs_name: str, outs_skills: List[str],
                 outs_daily_cost: float, outs_reliability: float,
                 outs_lead_time_days: int, outs_duration_multiplier: float = 1.5):
        self.outs_id = outs_id
        self.outs_name = outs_name
        self.outs_skills = outs_skills  # Навыки аутсорсера
        self.outs_daily_cost = outs_daily_cost
        self.outs_reliability = outs_reliability  # Общая надёжность (эффективность)
        self.outs_lead_time_days = outs_lead_time_days  # Задержка на онбординг
        self.outs_duration_multiplier = outs_duration_multiplier  # Множитель длительности задачи для аутсорсера (>1)

class Project:
    def __init__(self, proj_id=None):
        self.proj_id = proj_id
        self.proj_employees: Dict[int, Employee] = {}  # Словарь сотрудников
        self.proj_tasks: Dict[int, Task] = {}  # Словарь задач
        self.proj_dependencies: Dict[int, Dependency] = {}  # Словарь зависимостей
        self.proj_outsources: List[Outsource] = []  # Опции аутсорсинга
        self.proj_start_date = datetime.now()  # Дата начала проекта
        self.proj_current_date = datetime.now()  # Текущая дата симуляции (для анализа "что если")
        self.proj_simulation_results = {}  # Хранилище результатов симуляции Монте-Карло
        self._next_dep_id = 1 # Счётчик зависимостей
        

    def add_dependency(self, dep_from_task: int, dep_to_task: int, 
                   dep_type: str, dep_lag: float, dep_mandatory: bool = True):
        dep = Dependency(
            dep_id=self._next_dep_id,
            dep_from_task=dep_from_task,
            dep_to_task=dep_to_task,
            dep_type=dep_type,
            dep_lag=dep_lag,
            dep_mandatory=dep_mandatory
        )
        self.proj_dependencies[self._next_dep_id] = dep
        self._next_dep_id += 1
        return dep
    
class Assignment:
    def __init__(self, asg_task_id: int, asg_emp_id: int, 
                 asg_planned_start: datetime, asg_planned_end: datetime,
                 asg_hours_per_day: float):
        self.asg_task_id = asg_task_id  # Назначенная задача
        self.asg_emp_id = asg_emp_id  # Назначенный сотрудник
        self.asg_planned_start = asg_planned_start  # Плановая дата начала назначения
        self.asg_planned_end = asg_planned_end  # Плановая дата окончания назначения
        self.asg_hours_per_day = asg_hours_per_day  # Ежедневная рабочая нагрузка для этого назначения
        self.asg_actual_start = None
        self.asg_actual_end = None
        self.asg_progress = 0.0  # Прогресс назначения (0.0 - 1.0)
