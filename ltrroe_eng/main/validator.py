"""
LTRROE validator
Checks project-data integrity and consistency at all levels.
Protects data quality before simulation and analysis modules run.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any
from datetime import datetime

# Issue severity levels
class ValidationLevel(Enum):
    ERROR = "ERROR"      # critical, must be fixed
    WARNING = "WARNING"  # non-critical but suspicious
    INFO = "INFO"        # informational only

# Structure for one validation issue
@dataclass
class ValidationIssue:
    level: ValidationLevel  # severity level (ERROR/WARNING/INFO)
    message: str           # issue description
    object_type: str       # 'Employee', 'Task', 'Dependency', 'Outsource', 'Project'
    object_id: Any         # object ID such as emp_id, task_id, or dep_id
    field: str = None      # problematic field
    value: Any = None      # problematic value

class LTRROEValidator:
    def __init__(self):
        self.issues = []  # all discovered issues are stored here

    def validate_project(self, project) -> dict:
        """
        Main method: validate the whole project.
        Returns a dictionary with validation results.
        """
        self.issues.clear()

        self._check_project_basics(project)
        self._validate_all_employees(project)
        self._validate_all_tasks(project)
        self._validate_dependencies(project)
        self._validate_outsources(project)
        # self._validate_assignments(project)  # currently skipped

        return self._create_report()

    def _add_issue(self, level: ValidationLevel, message: str,
                  object_type: str, object_id: Any,
                  field: str = None, value: Any = None):
        """Add an issue to the list."""
        self.issues.append(ValidationIssue(
            level=level,
            message=message,
            object_type=object_type,
            object_id=object_id,
            field=field,
            value=value
        ))

    def _check_project_basics(self, project):
        """Validate basic project components."""
        if not hasattr(project, 'proj_tasks'):
            self._add_issue(ValidationLevel.ERROR,
                          "Project has no task dictionary",
                          'Project', 'project', 'proj_tasks')
        elif not project.proj_tasks:
            self._add_issue(ValidationLevel.WARNING,
                          "Project has no tasks",
                          'Project', 'project')

        if not hasattr(project, 'proj_employees'):
            self._add_issue(ValidationLevel.ERROR,
                          "Project has no employee dictionary",
                          'Project', 'project', 'proj_employees')
        elif not project.proj_employees:
            self._add_issue(ValidationLevel.WARNING,
                          "Project has no employees",
                          'Project', 'project')

        if not hasattr(project, 'proj_dependencies'):
            self._add_issue(ValidationLevel.ERROR,
                          "Project has no dependency dictionary",
                          'Project', 'project', 'proj_dependencies')

        if hasattr(project, 'proj_start_date'):
            if not isinstance(project.proj_start_date, datetime):
                self._add_issue(ValidationLevel.ERROR,
                              "Invalid project start-date type",
                              'Project', 'project',
                              'proj_start_date',
                              type(project.proj_start_date))
        else:
            self._add_issue(ValidationLevel.ERROR,
                          "Project has no start date",
                          'Project', 'project', 'proj_start_date')

        if not hasattr(project, '_next_dep_id'):
            self._add_issue(ValidationLevel.WARNING,
                          "Project has no dependency ID counter",
                          'Project', 'project', '_next_dep_id')
        elif not isinstance(project._next_dep_id, int):
            self._add_issue(ValidationLevel.ERROR,
                          "Dependency ID counter must be an integer",
                          'Project', 'project', '_next_dep_id',
                          type(project._next_dep_id))

    def _validate_all_employees(self, project):
        """Validate all employees."""
        if not hasattr(project, 'proj_employees'):
            return

        for emp_id, employee in project.proj_employees.items():
            self._validate_employee(employee, emp_id)

    def _validate_employee(self, employee, emp_id):
        """Validate one employee."""
        required_fields = ["emp_name", "emp_skills", "emp_efficiency"]
        for field in required_fields:
            if not hasattr(employee, field):
                self._add_issue(ValidationLevel.ERROR,
                              f"Missing field {field} in employee",
                              'Employee', emp_id, field)

        if hasattr(employee, 'emp_name'):
            if not employee.emp_name:
                self._add_issue(ValidationLevel.ERROR,
                              "Employee name is missing",
                              'Employee', emp_id,
                              'emp_name', employee.emp_name)
            elif not isinstance(employee.emp_name, str):
                self._add_issue(ValidationLevel.ERROR,
                              "Employee name must be a string",
                              'Employee', emp_id,
                              'emp_name', type(employee.emp_name))
            elif not employee.emp_name.strip():
                self._add_issue(ValidationLevel.ERROR,
                              "Employee name contains only whitespace",
                              'Employee', emp_id,
                              'emp_name', employee.emp_name)

        if hasattr(employee, 'emp_skills'):
            if not isinstance(employee.emp_skills, list):
                self._add_issue(ValidationLevel.ERROR,
                              "Skills must be a list",
                              'Employee', emp_id,
                              'emp_skills', type(employee.emp_skills))
            elif not employee.emp_skills:
                self._add_issue(ValidationLevel.WARNING,
                              "Employee has no listed skills",
                              'Employee', emp_id,
                              'emp_skills', employee.emp_skills)
            else:
                for skill in employee.emp_skills:
                    if not isinstance(skill, str):
                        self._add_issue(ValidationLevel.ERROR,
                                      "Skill must be a string",
                                      'Employee', emp_id,
                                      f'emp_skills[{skill}]', type(skill))

        if hasattr(employee, 'emp_error_prob'):
            if not isinstance(employee.emp_error_prob, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Error probability must be numeric",
                              'Employee', emp_id,
                              'emp_error_prob', employee.emp_error_prob)
            elif not 0.0 <= employee.emp_error_prob <= 1.0:
                self._add_issue(ValidationLevel.ERROR,
                              "Error probability must be in the 0.0-1.0 range",
                              'Employee', emp_id,
                              'emp_error_prob', employee.emp_error_prob)

        if hasattr(employee, 'emp_cost_per_hour'):
            if not isinstance(employee.emp_cost_per_hour, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Hourly cost must be numeric",
                              'Employee', emp_id,
                              'emp_cost_per_hour', employee.emp_cost_per_hour)
            elif employee.emp_cost_per_hour < 0:
                self._add_issue(ValidationLevel.WARNING,
                              "Hourly cost is negative",
                              'Employee', emp_id,
                              'emp_cost_per_hour', employee.emp_cost_per_hour)

        if hasattr(employee, 'emp_efficiency'):
            if not isinstance(employee.emp_efficiency, dict):
                self._add_issue(ValidationLevel.ERROR,
                              "Efficiency must be a {skill: efficiency} dictionary",
                              'Employee', emp_id,
                              'emp_efficiency', type(employee.emp_efficiency))
            else:
                for skill, efficiency in employee.emp_efficiency.items():
                    if not isinstance(efficiency, (int, float)):
                        self._add_issue(ValidationLevel.ERROR,
                                      f"Skill efficiency '{skill}' must be numeric",
                                      'Employee', emp_id,
                                      f'emp_efficiency[{skill}]', efficiency)
                    elif not 0.0 <= efficiency <= 10.0:
                        self._add_issue(ValidationLevel.ERROR,
                                      f"Skill efficiency '{skill}' must be in the 0.0-10.0 range",
                                      'Employee', emp_id,
                                      f'emp_efficiency[{skill}]', efficiency)

        if hasattr(employee, 'emp_max_daily_hours'):
            if not isinstance(employee.emp_max_daily_hours, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Maximum daily workload must be numeric",
                              'Employee', emp_id,
                              'emp_max_daily_hours', employee.emp_max_daily_hours)
            elif employee.emp_max_daily_hours <= 0:
                self._add_issue(ValidationLevel.ERROR,
                              "Maximum daily workload must be positive",
                              'Employee', emp_id,
                              'emp_max_daily_hours', employee.emp_max_daily_hours)
            elif employee.emp_max_daily_hours > 24:
                self._add_issue(ValidationLevel.WARNING,
                              "Maximum daily workload exceeds 24 hours per day",
                              'Employee', emp_id,
                              'emp_max_daily_hours', employee.emp_max_daily_hours)

        if hasattr(employee, 'emp_current_load'):
            if not isinstance(employee.emp_current_load, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Current workload must be numeric",
                              'Employee', emp_id,
                              'emp_current_load', employee.emp_current_load)
            elif employee.emp_current_load < 0:
                self._add_issue(ValidationLevel.WARNING,
                              "Current workload is negative",
                              'Employee', emp_id,
                              'emp_current_load', employee.emp_current_load)

            if hasattr(employee, 'emp_max_daily_hours'):
                if employee.emp_current_load > employee.emp_max_daily_hours:
                    self._add_issue(ValidationLevel.WARNING,
                                  f"Current workload ({employee.emp_current_load}) exceeds the maximum ({employee.emp_max_daily_hours})",
                                  'Employee', emp_id,
                                  'emp_current_load', employee.emp_current_load)

        if hasattr(employee, 'emp_fatigue'):
            if not isinstance(employee.emp_fatigue, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Fatigue multiplier must be numeric",
                              'Employee', emp_id,
                              'emp_fatigue', employee.emp_fatigue)
            elif employee.emp_fatigue <= 0:
                self._add_issue(ValidationLevel.WARNING,
                              "Fatigue multiplier is not positive",
                              'Employee', emp_id,
                              'emp_fatigue', employee.emp_fatigue)

        if hasattr(employee, 'emp_assigned_tasks'):
            if not isinstance(employee.emp_assigned_tasks, list):
                self._add_issue(ValidationLevel.ERROR,
                              "Assigned tasks must be a list",
                              'Employee', emp_id,
                              'emp_assigned_tasks', type(employee.emp_assigned_tasks))

    def _validate_all_tasks(self, project):
        """Validate all tasks."""
        if not hasattr(project, 'proj_tasks'):
            return

        for task_id, task in project.proj_tasks.items():
            self._validate_task(task, task_id)

    def _validate_task(self, task, task_id):
        """Validate one task."""
        required_fields = ["task_name", "task_skills", "task_duration_dist"]
        for field in required_fields:
            if not hasattr(task, field):
                self._add_issue(ValidationLevel.ERROR,
                              f"Missing field {field} in task",
                              'Task', task_id, field)

        if hasattr(task, 'task_name'):
            if not task.task_name:
                self._add_issue(ValidationLevel.ERROR,
                              "Task name is missing",
                              'Task', task_id,
                              'task_name', task.task_name)
            elif not isinstance(task.task_name, str):
                self._add_issue(ValidationLevel.ERROR,
                              "Task name must be a string",
                              'Task', task_id,
                              'task_name', type(task.task_name))
            elif not task.task_name.strip():
                self._add_issue(ValidationLevel.ERROR,
                              "Task name contains only whitespace",
                              'Task', task_id,
                              'task_name', task.task_name)

        if hasattr(task, 'task_skills'):
            if not isinstance(task.task_skills, list):
                self._add_issue(ValidationLevel.ERROR,
                              "Required skills must be a list",
                              'Task', task_id,
                              'task_skills', type(task.task_skills))
            elif not task.task_skills:
                self._add_issue(ValidationLevel.WARNING,
                              "Task has no required skills",
                              'Task', task_id,
                              'task_skills', task.task_skills)
            else:
                for skill in task.task_skills:
                    if not isinstance(skill, str):
                        self._add_issue(ValidationLevel.ERROR,
                                      "Required skill must be a string",
                                      'Task', task_id,
                                      f'task_skills[{skill}]', type(skill))

        if hasattr(task, 'task_crit'):
            if not isinstance(task.task_crit, int):
                self._add_issue(ValidationLevel.ERROR,
                              "Criticality must be an integer",
                              'Task', task_id,
                              'task_crit', task.task_crit)
            elif not 1 <= task.task_crit <= 5:
                self._add_issue(ValidationLevel.ERROR,
                              "Criticality must be in the 1-5 range",
                              'Task', task_id,
                              'task_crit', task.task_crit)

        if hasattr(task, 'task_cost'):
            if not isinstance(task.task_cost, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Task cost must be numeric",
                              'Task', task_id,
                              'task_cost', task.task_cost)
            elif task.task_cost < 0:
                self._add_issue(ValidationLevel.WARNING,
                              "Task cost is negative",
                              'Task', task_id,
                              'task_cost', task.task_cost)

        if hasattr(task, 'task_duration_dist'):
            if not isinstance(task.task_duration_dist, (list, tuple)):
                self._add_issue(ValidationLevel.ERROR,
                              "task_duration_dist must be a list or tuple",
                              'Task', task_id,
                              'task_duration_dist', task.task_duration_dist)
            elif len(task.task_duration_dist) != 3:
                self._add_issue(ValidationLevel.ERROR,
                              f"task_duration_dist must contain 3 elements (got {len(task.task_duration_dist)})",
                              'Task', task_id,
                              'task_duration_dist', task.task_duration_dist)
            else:
                if not all(isinstance(x, (int, float)) for x in task.task_duration_dist):
                    self._add_issue(ValidationLevel.ERROR,
                                  "All duration values must be numeric",
                                  'Task', task_id,
                                  'task_duration_dist', task.task_duration_dist)
                else:
                    if not (task.task_duration_dist[0] <= task.task_duration_dist[1] <= task.task_duration_dist[2]):
                        self._add_issue(ValidationLevel.ERROR,
                                      f"Durations must be ordered as optimistic <= likely <= pessimistic (got {task.task_duration_dist})",
                                      'Task', task_id,
                                      'task_duration_dist', task.task_duration_dist)
                    if any(x <= 0 for x in task.task_duration_dist):
                        self._add_issue(ValidationLevel.ERROR,
                                      "Duration must be positive",
                                      'Task', task_id,
                                      'task_duration_dist', task.task_duration_dist)

        if hasattr(task, 'task_assigned_to'):
            if not isinstance(task.task_assigned_to, list):
                self._add_issue(ValidationLevel.ERROR,
                              "task_assigned_to must be a list",
                              'Task', task_id,
                              'task_assigned_to', task.task_assigned_to)
            else:
                for emp_id in task.task_assigned_to:
                    if not isinstance(emp_id, (int, str)):
                        self._add_issue(ValidationLevel.ERROR,
                                      f"Assigned employee ID must be a string or integer: {emp_id}",
                                      'Task', task_id,
                                      'task_assigned_to', emp_id)

        if hasattr(task, 'task_status'):
            valid_statuses = ['not_started', 'in_progress', 'completed', 'blocked']
            if task.task_status not in valid_statuses:
                self._add_issue(ValidationLevel.WARNING,
                              f"Unknown task status: {task.task_status}",
                              'Task', task_id,
                              'task_status', task.task_status)

        if hasattr(task, 'task_actual_duration'):
            if task.task_actual_duration is not None:
                if not isinstance(task.task_actual_duration, (int, float)):
                    self._add_issue(ValidationLevel.ERROR,
                                  "Actual duration must be numeric",
                                  'Task', task_id,
                                  'task_actual_duration', task.task_actual_duration)
                elif task.task_actual_duration <= 0:
                    self._add_issue(ValidationLevel.WARNING,
                                  "Actual duration is not positive",
                                  'Task', task_id,
                                  'task_actual_duration', task.task_actual_duration)

        if hasattr(task, 'task_primary_assignee'):
            if task.task_primary_assignee is not None:
                if not isinstance(task.task_primary_assignee, (int, str)):
                    self._add_issue(ValidationLevel.ERROR,
                                  "Primary assignee must be a string or integer ID",
                                  'Task', task_id,
                                  'task_primary_assignee', task.task_primary_assignee)

    def _validate_dependencies(self, project):
        """Validate all dependencies."""
        if not hasattr(project, 'proj_dependencies'):
            return

        if not project.proj_dependencies:
            return

        task_ids = set(project.proj_tasks.keys()) if project.proj_tasks else set()

        # Support both dictionary and list storage for backward compatibility
        if isinstance(project.proj_dependencies, dict):
            items = project.proj_dependencies.items()
        elif isinstance(project.proj_dependencies, list):
            items = enumerate(project.proj_dependencies)
        else:
            self._add_issue(ValidationLevel.ERROR,
                            "proj_dependencies must be a list or dictionary",
                            'Project', 'project', 'proj_dependencies')
            return

        for dep_id, dependency in items:
            self._validate_dependency(dependency, dep_id, task_ids)

    def _validate_dependency(self, dependency, dep_id, task_ids):
        """Validate one dependency."""
        if hasattr(dependency, 'dep_id') and dependency.dep_id is not None:
            if not isinstance(dependency.dep_id, int):
                self._add_issue(ValidationLevel.ERROR,
                              "Dependency ID must be an integer",
                              'Dependency', dep_id,
                              'dep_id', dependency.dep_id)

        if not isinstance(dependency.dep_from_task, (int, str)):
            self._add_issue(ValidationLevel.ERROR,
                          "dep_from_task must be a string or integer",
                          'Dependency', dep_id,
                          'dep_from_task', dependency.dep_from_task)
        elif dependency.dep_from_task not in task_ids:
            self._add_issue(ValidationLevel.ERROR,
                          f"Predecessor task {dependency.dep_from_task} does not exist in the project",
                          'Dependency', dep_id,
                          'dep_from_task', dependency.dep_from_task)

        if not isinstance(dependency.dep_to_task, (int, str)):
            self._add_issue(ValidationLevel.ERROR,
                          "dep_to_task must be a string or integer",
                          'Dependency', dep_id,
                          'dep_to_task', dependency.dep_to_task)
        elif dependency.dep_to_task not in task_ids:
            self._add_issue(ValidationLevel.ERROR,
                          f"Successor task {dependency.dep_to_task} does not exist in the project",
                          'Dependency', dep_id,
                          'dep_to_task', dependency.dep_to_task)

        if dependency.dep_from_task == dependency.dep_to_task:
            self._add_issue(ValidationLevel.ERROR,
                          "A task cannot depend on itself",
                          'Dependency', dep_id)

        valid_dep_types = ["FS", "SS", "FF", "SF"]
        if dependency.dep_type not in valid_dep_types:
            self._add_issue(ValidationLevel.ERROR,
                          f"Unknown dependency type: {dependency.dep_type}",
                          'Dependency', dep_id,
                          'dep_type', dependency.dep_type)

        if not isinstance(dependency.dep_lag, (int, float)):
            self._add_issue(ValidationLevel.ERROR,
                          "Lag must be numeric",
                          'Dependency', dep_id,
                          'dep_lag', dependency.dep_lag)
        elif dependency.dep_lag < 0:
            self._add_issue(ValidationLevel.WARNING,
                          f"Negative lag ({dependency.dep_lag}) can cause problems",
                          'Dependency', dep_id,
                          'dep_lag', dependency.dep_lag)

        if not isinstance(dependency.dep_mandatory, bool):
            self._add_issue(ValidationLevel.ERROR,
                          "dep_mandatory must be boolean",
                          'Dependency', dep_id,
                          'dep_mandatory', dependency.dep_mandatory)

    def _validate_outsources(self, project):
        """Validate outsource options."""
        if not hasattr(project, 'proj_outsources'):
            return
        if not project.proj_outsources:
            return

        for i, outsource in enumerate(project.proj_outsources):
            self._validate_outsource(outsource, i)

    def _validate_outsource(self, outsource, outs_id):
        """Validate one outsource option."""
        if not hasattr(outsource, 'outs_id'):
            self._add_issue(ValidationLevel.ERROR,
                          "Outsource provider has no ID",
                          'Outsource', outs_id)
        elif not isinstance(outsource.outs_id, int):
            self._add_issue(ValidationLevel.ERROR,
                          "Outsource provider ID must be an integer",
                          'Outsource', outs_id,
                          'outs_id', outsource.outs_id)

        if not hasattr(outsource, 'outs_name'):
            self._add_issue(ValidationLevel.ERROR,
                          "Outsource provider has no name",
                          'Outsource', outs_id,
                          'outs_name')
        elif not outsource.outs_name or not isinstance(outsource.outs_name, str):
            self._add_issue(ValidationLevel.ERROR,
                          "Outsource provider name must be a non-empty string",
                          'Outsource', outs_id,
                          'outs_name', outsource.outs_name)

        if hasattr(outsource, 'outs_skills'):
            if not isinstance(outsource.outs_skills, list):
                self._add_issue(ValidationLevel.ERROR,
                              "Outsource provider skills must be a list",
                              'Outsource', outs_id,
                              'outs_skills', type(outsource.outs_skills))

        if hasattr(outsource, 'outs_daily_cost'):
            if not isinstance(outsource.outs_daily_cost, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Daily cost must be numeric",
                              'Outsource', outs_id,
                              'outs_daily_cost', outsource.outs_daily_cost)
            elif outsource.outs_daily_cost < 0:
                self._add_issue(ValidationLevel.WARNING,
                              "Daily cost is negative",
                              'Outsource', outs_id,
                              'outs_daily_cost', outsource.outs_daily_cost)

        if hasattr(outsource, 'outs_reliability'):
            if not isinstance(outsource.outs_reliability, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Reliability must be numeric",
                              'Outsource', outs_id,
                              'outs_reliability', outsource.outs_reliability)
            elif not 0.0 <= outsource.outs_reliability <= 1.0:
                self._add_issue(ValidationLevel.ERROR,
                              "Reliability must be in the 0.0-1.0 range",
                              'Outsource', outs_id,
                              'outs_reliability', outsource.outs_reliability)

        if hasattr(outsource, 'outs_lead_time_days'):
            if not isinstance(outsource.outs_lead_time_days, int):
                self._add_issue(ValidationLevel.ERROR,
                              "Lead time must be an integer number of days",
                              'Outsource', outs_id,
                              'outs_lead_time_days', outsource.outs_lead_time_days)
            elif outsource.outs_lead_time_days < 0:
                self._add_issue(ValidationLevel.WARNING,
                              "Lead time is negative",
                              'Outsource', outs_id,
                              'outs_lead_time_days', outsource.outs_lead_time_days)

        if hasattr(outsource, 'outs_duration_multiplier'):
            if not isinstance(outsource.outs_duration_multiplier, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Duration multiplier must be numeric",
                              'Outsource', outs_id,
                              'outs_duration_multiplier', outsource.outs_duration_multiplier)
            elif outsource.outs_duration_multiplier <= 0:
                self._add_issue(ValidationLevel.ERROR,
                              "Duration multiplier must be positive",
                              'Outsource', outs_id,
                              'outs_duration_multiplier', outsource.outs_duration_multiplier)
            elif outsource.outs_duration_multiplier < 1.0:
                self._add_issue(ValidationLevel.WARNING,
                              "Duration multiplier is below 1.0, meaning the outsource provider is faster than the internal team",
                              'Outsource', outs_id,
                              'outs_duration_multiplier', outsource.outs_duration_multiplier)

    def _create_report(self) -> dict:
        """Build the final validation report."""
        errors = [issue for issue in self.issues if issue.level == ValidationLevel.ERROR]
        warnings = [issue for issue in self.issues if issue.level == ValidationLevel.WARNING]
        infos = [issue for issue in self.issues if issue.level == ValidationLevel.INFO]

        return {
            "total_issues": len(self.issues),
            "errors": len(errors),
            "warnings": len(warnings),
            "infos": len(infos),
            "is_valid": len(errors) == 0,
            "issues_by_type": {
                "Employee": len([i for i in self.issues if i.object_type == 'Employee']),
                "Task": len([i for i in self.issues if i.object_type == 'Task']),
                "Dependency": len([i for i in self.issues if i.object_type == 'Dependency']),
                "Outsource": len([i for i in self.issues if i.object_type == 'Outsource']),
                "Project": len([i for i in self.issues if i.object_type == 'Project']),
            },
            "issues": [
                {
                    "level": issue.level.value,
                    "message": issue.message,
                    "object_type": issue.object_type,
                    "object_id": issue.object_id,
                    "field": issue.field,
                    "value": str(issue.value) if issue.value is not None else None
                }
                for issue in self.issues
            ],
            "summary": {
                "errors": [
                    f"{issue.object_type} {issue.object_id}: {issue.message}"
                    for issue in errors
                ],
                "warnings": [
                    f"{issue.object_type} {issue.object_id}: {issue.message}"
                    for issue in warnings
                ]
            }
        }

    def print_report(self, report: dict):
        """Print the validation report in a readable format."""
        print("=" * 60)
        print("PROJECT VALIDATION RESULTS")
        print("=" * 60)

        if report["is_valid"]:
            print("✓ Project is valid")
        else:
            print(f"✗ Errors found: {report['errors']}")

        print(f"  Warnings: {report['warnings']}")
        print(f"  Informational messages: {report['infos']}")
        print(f"  Total issues: {report['total_issues']}")

        if report["issues_by_type"]:
            print("\nIssues by object type:")
            for obj_type, count in report["issues_by_type"].items():
                if count > 0:
                    print(f"  {obj_type}: {count}")

        if report["summary"]["errors"]:
            print("\nERRORS TO FIX:")
            for i, error in enumerate(report["summary"]["errors"], 1):
                print(f"  {i}. {error}")

        if report["summary"]["warnings"]:
            print("\nWARNINGS TO REVIEW:")
            for i, warning in enumerate(report["summary"]["warnings"], 1):
                print(f"  {i}. {warning}")

        print("=" * 60)
