"""
LTRROE data models
Defines the main classes and structures used to represent project entities
Used in the research prototype for typed, structured data storage

Main classes:
- Task: project task with duration, criticality, and required skills
- Employee: team member with skills, workload, and error-probability attributes
- Project: container that combines tasks, employees, and dependencies
- Dependency: typed task relation with a time lag
- Outsource: external execution option for a task
- Assignment: task assignment to an employee

Architecture:
Classes include helper methods for common operations and derived parameters.
Each class contains the attributes required for modeling and analysis.
"""
 
from datetime import datetime
from typing import Dict, List, Optional, Union

EntityId = Union[int, str]

class Employee:
    def __init__(self, emp_id: EntityId, emp_name: str, emp_skills: List[str],
                 emp_error_prob: float, emp_cost_per_hour: float,
                 emp_efficiency: Dict[str, float]):
        self.emp_id = emp_id
        self.emp_name = emp_name
        self.emp_skills = emp_skills  # Employee skill list
        self.emp_error_prob = emp_error_prob 
        self.emp_cost_per_hour = emp_cost_per_hour
        self.emp_efficiency = emp_efficiency  # Skill efficiency, where 0.6 = 60% and 1.2 = 120% of baseline
        self.emp_max_daily_hours = 8.0
        self.emp_current_load = 0.0
        self.emp_fatigue = 1.0  # Fatigue multiplier: >1 tired, <1 rested; affects error rate and speed
        self.emp_assigned_tasks = []  # Currently assigned tasks

class Task:
    def __init__(self, task_id: EntityId, task_name: str, task_skills: List[str], 
                 task_crit: int, task_cost: float, task_duration_dist: tuple):
        self.task_id = task_id
        self.task_name = task_name
        self.task_skills = task_skills  # Skills required by the task
        self.task_crit = task_crit  # Task criticality from 1 to 5, where 5 is the highest priority
        self.task_cost = task_cost
        self.task_duration_dist = task_duration_dist
        self.task_assigned_to = []  # Assigned employees
        self.task_status = "in_progress"  # Current status; allowed values: ['not_started', 'in_progress', 'completed', 'blocked']
        self.task_actual_duration = None
        self.task_primary_assignee = None 

class Dependency:
    def __init__(self, dep_from_task: EntityId, dep_to_task: EntityId, 
                 dep_type: str, dep_lag: float, 
                 dep_mandatory: bool = True, dep_id: Optional[int] = None):
        self.dep_id = dep_id
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
        self.outs_skills = outs_skills  # Outsource provider skills
        self.outs_daily_cost = outs_daily_cost
        self.outs_reliability = outs_reliability  # Overall reliability/efficiency
        self.outs_lead_time_days = outs_lead_time_days  # Onboarding lead time
        self.outs_duration_multiplier = outs_duration_multiplier  # Task-duration multiplier for the outsource provider (>1)

class Project:
    def __init__(self, proj_id=None):
        self.proj_id = proj_id
        self.proj_employees: Dict[EntityId, Employee] = {}  # Employee dictionary
        self.proj_tasks: Dict[EntityId, Task] = {}  # Task dictionary
        self.proj_dependencies: Dict[int, Dependency] = {}  # Dependency dictionary
        self.proj_outsources: List[Outsource] = []  # Outsource options
        self.proj_start_date = datetime.now()  # Project start date
        self.proj_current_date = datetime.now()  # Current simulation date for what-if analysis
        self.proj_simulation_results = {}  # Monte Carlo simulation result storage
        self._next_dep_id = 1 # Dependency ID counter
        

    def add_dependency(self, dep_from_task: EntityId, dep_to_task: EntityId, 
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
    def __init__(self, asg_task_id: EntityId, asg_emp_id: EntityId, 
                 asg_planned_start: datetime, asg_planned_end: datetime,
                 asg_hours_per_day: float):
        self.asg_task_id = asg_task_id  # Assigned task
        self.asg_emp_id = asg_emp_id  # Assigned employee
        self.asg_planned_start = asg_planned_start  # Planned assignment start date
        self.asg_planned_end = asg_planned_end  # Planned assignment end date
        self.asg_hours_per_day = asg_hours_per_day  # Daily workload for this assignment
        self.asg_actual_start = None
        self.asg_actual_end = None
        self.asg_progress = 0.0  # Assignment progress from 0.0 to 1.0
