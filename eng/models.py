"""
LTRROE System Data Models
Defines core classes and structures for project entity representation
Used within research prototype to ensure typing and structured data storage

Core Classes:
- Task: Project task with duration, criticality, required skills attributes
- Employee: Team member with competency, workload, error probability characteristics
- Project: Project container unifying tasks, employees and dependencies
- Dependency: Task-to-task relationship with type and lag
- Outsource: Task outsourcing option
- Assignment: Task-to-employee allocation

Architecture:
Classes implemented with methods for convenient operations and derived parameter calculations.
Each class contains all necessary attributes for simulation and analysis.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional

class Employee:
    def __init__(self, emp_id: int, emp_name: str, emp_skills: List[str],
                 emp_error_prob: float, emp_cost_per_hour: float,
                 emp_efficiency: Dict[str, float]):
        self.emp_id = emp_id
        self.emp_name = emp_name
        self.emp_skills = emp_skills  # List of employee skills
        self.emp_error_prob = emp_error_prob 
        self.emp_cost_per_hour = emp_cost_per_hour
        self.emp_efficiency = emp_efficiency  # Skill efficiency (0.6 = 60%, 1.2 = 120% of baseline)
        self.emp_max_daily_hours = 8.0
        self.emp_current_load = 0.0
        self.emp_fatigue = 1.0  # Fatigue multiplier: >1 = fatigued, <1 = rested (affects errors and speed)
        self.emp_assigned_tasks = []  # Currently assigned tasks

class Task:
    def __init__(self, task_id: int, task_name: str, task_skills: List[str], 
                 task_crit: int, task_cost: float, task_duration_dist: tuple):
        self.task_id = task_id
        self.task_name = task_name
        self.task_skills = task_skills  # Required skills for the task
        self.task_crit = task_crit  # Task criticality (1-5), 5 = highest priority
        self.task_cost = task_cost
        self.task_duration_dist = task_duration_dist
        self.task_assigned_to = []  # Assigned employees
        self.task_status = "in_progress"  # Current status; valid_statuses = ['not_started', 'in_progress', 'completed', 'blocked']
        self.task_actual_duration = None
        self.task_primary_assignee = None 

class Dependency:
    def __init__(self, dep_from_task: int, dep_to_task: int, 
                 dep_type: str, dep_lag: float, dep_mandatory: bool = True):
        self.dep_from_task = dep_from_task  # Predecessor task
        self.dep_to_task = dep_to_task  # Successor task
        self.dep_type = dep_type  # "FS", "SS", "FF", "SF"
        self.dep_lag = dep_lag  # Lag in days
        self.dep_mandatory = dep_mandatory

class Outsource:
    def __init__(self, outs_id: int, outs_name: str, outs_skills: List[str],
                 outs_daily_cost: float, outs_reliability: float,
                 outs_lead_time_days: int, outs_duration_multiplier: float = 1.5):
        self.outs_id = outs_id
        self.outs_name = outs_name
        self.outs_skills = outs_skills  # Outsourcer skills
        self.outs_daily_cost = outs_daily_cost
        self.outs_reliability = outs_reliability  # Overall reliability (efficiency)
        self.outs_lead_time_days = outs_lead_time_days  # Onboarding delay
        self.outs_duration_multiplier = outs_duration_multiplier  # Task duration multiplier for outsourcer (>1)

class Project:
    def __init__(self):
        self.proj_employees: Dict[int, Employee] = {}  # Employee dictionary
        self.proj_tasks: Dict[int, Task] = {}  # Task dictionary
        self.proj_dependencies: List[Dependency] = []  # Dependency list
        self.proj_outsources: List[Outsource] = []  # Outsourcing options
        self.proj_start_date = datetime.now()  # Project start date
        self.proj_current_date = datetime.now()  # Current simulation date (for "what-if" analysis)
        self.proj_simulation_results = {}  # Monte Carlo simulation results storage

class Assignment:
    def __init__(self, asg_task_id: int, asg_emp_id: int, 
                 asg_planned_start: datetime, asg_planned_end: datetime,
                 asg_hours_per_day: float):
        self.asg_task_id = asg_task_id  # Assigned task
        self.asg_emp_id = asg_emp_id  # Assigned employee
        self.asg_planned_start = asg_planned_start  # Planned assignment start date
        self.asg_planned_end = asg_planned_end  # Planned assignment end date
        self.asg_hours_per_day = asg_hours_per_day  # Daily workload hours for this assignment
        self.asg_actual_start = None
        self.asg_actual_end = None
        self.asg_progress = 0.0  # Assignment progress (0.0 to 1.0)
