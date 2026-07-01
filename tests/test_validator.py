"""
Валидатор системы LTRROE
Проверяет целостность и согласованность данных проекта на всех уровнях.
Обеспечивает качество данных для модулей симуляции и анализа.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any
from datetime import datetime

# Уровни серьёзности проблем
class ValidationLevel(Enum):
    ERROR = "ERROR"      # критично, нужно исправить
    WARNING = "WARNING"  # не критично, но странно
    INFO = "INFO"        # просто информация

# Структура для одной найденной проблемы
@dataclass
class ValidationIssue:
    level: ValidationLevel  # уровень (ERROR/WARNING/INFO)
    message: str           # описание проблемы
    object_type: str       # 'Employee', 'Task', 'Dependency', 'Outsource', 'Project'
    object_id: Any         # ID объекта (emp_id, task_id, dep_id и т.д.)
    field: str = None      # какое поле проблемное
    value: Any = None      # проблемное значение

class LTRROEValidator:
    def __init__(self):
        self.issues = []  # здесь будут все найденные проблемы

    def validate_project(self, project) -> dict:
        """
        Главный метод: проверяет весь проект.
        Возвращает словарь с результатами валидации.
        """
        self.issues.clear()

        self._check_project_basics(project)
        self._validate_all_employees(project)
        self._validate_all_tasks(project)
        self._validate_dependencies(project)
        self._validate_outsources(project)
        # self._validate_assignments(project)  # пока пропущено

        return self._create_report()

    def _add_issue(self, level: ValidationLevel, message: str,
                  object_type: str, object_id: Any,
                  field: str = None, value: Any = None):
        """Добавляет проблему в список."""
        self.issues.append(ValidationIssue(
            level=level,
            message=message,
            object_type=object_type,
            object_id=object_id,
            field=field,
            value=value
        ))

    def _check_project_basics(self, project):
        """Проверка базовых компонентов проекта."""
        if not hasattr(project, 'proj_tasks'):
            self._add_issue(ValidationLevel.ERROR,
                          "Проект не содержит словаря задач",
                          'Project', 'project', 'proj_tasks')
        elif not project.proj_tasks:
            self._add_issue(ValidationLevel.WARNING,
                          "В проекте нет задач",
                          'Project', 'project')

        if not hasattr(project, 'proj_employees'):
            self._add_issue(ValidationLevel.ERROR,
                          "Проект не содержит словаря сотрудников",
                          'Project', 'project', 'proj_employees')
        elif not project.proj_employees:
            self._add_issue(ValidationLevel.WARNING,
                          "В проекте нет сотрудников",
                          'Project', 'project')

        if not hasattr(project, 'proj_dependencies'):
            self._add_issue(ValidationLevel.ERROR,
                          "Проект не содержит словаря зависимостей",
                          'Project', 'project', 'proj_dependencies')

        if hasattr(project, 'proj_start_date'):
            if not isinstance(project.proj_start_date, datetime):
                self._add_issue(ValidationLevel.ERROR,
                              "Некорректный тип даты начала проекта",
                              'Project', 'project',
                              'proj_start_date',
                              type(project.proj_start_date))
        else:
            self._add_issue(ValidationLevel.ERROR,
                          "Проект не имеет даты начала",
                          'Project', 'project', 'proj_start_date')

        if not hasattr(project, '_next_dep_id'):
            self._add_issue(ValidationLevel.WARNING,
                          "Проект не имеет счётчика ID зависимостей",
                          'Project', 'project', '_next_dep_id')
        elif not isinstance(project._next_dep_id, int):
            self._add_issue(ValidationLevel.ERROR,
                          "Счётчик ID зависимостей должен быть целым числом",
                          'Project', 'project', '_next_dep_id',
                          type(project._next_dep_id))

    def _validate_all_employees(self, project):
        """Проверка всех сотрудников."""
        if not hasattr(project, 'proj_employees'):
            return

        for emp_id, employee in project.proj_employees.items():
            self._validate_employee(employee, emp_id)

    def _validate_employee(self, employee, emp_id):
        """Проверка одного сотрудника."""
        required_fields = ["emp_name", "emp_skills", "emp_efficiency"]
        for field in required_fields:
            if not hasattr(employee, field):
                self._add_issue(ValidationLevel.ERROR,
                              f"Отсутствует поле {field} у сотрудника",
                              'Employee', emp_id, field)

        if hasattr(employee, 'emp_name'):
            if not employee.emp_name:
                self._add_issue(ValidationLevel.ERROR,
                              "Имя сотрудника отсутствует",
                              'Employee', emp_id,
                              'emp_name', employee.emp_name)
            elif not isinstance(employee.emp_name, str):
                self._add_issue(ValidationLevel.ERROR,
                              "Имя сотрудника должно быть строкой",
                              'Employee', emp_id,
                              'emp_name', type(employee.emp_name))
            elif not employee.emp_name.strip():
                self._add_issue(ValidationLevel.ERROR,
                              "Имя сотрудника состоит только из пробелов",
                              'Employee', emp_id,
                              'emp_name', employee.emp_name)

        if hasattr(employee, 'emp_skills'):
            if not isinstance(employee.emp_skills, list):
                self._add_issue(ValidationLevel.ERROR,
                              "Навыки должны быть списком",
                              'Employee', emp_id,
                              'emp_skills', type(employee.emp_skills))
            elif not employee.emp_skills:
                self._add_issue(ValidationLevel.WARNING,
                              "У сотрудника нет указанных навыков",
                              'Employee', emp_id,
                              'emp_skills', employee.emp_skills)
            else:
                for skill in employee.emp_skills:
                    if not isinstance(skill, str):
                        self._add_issue(ValidationLevel.ERROR,
                                      "Навык должен быть строкой",
                                      'Employee', emp_id,
                                      f'emp_skills[{skill}]', type(skill))

        if hasattr(employee, 'emp_error_prob'):
            if not isinstance(employee.emp_error_prob, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Вероятность ошибки должна быть числом",
                              'Employee', emp_id,
                              'emp_error_prob', employee.emp_error_prob)
            elif not 0.0 <= employee.emp_error_prob <= 1.0:
                self._add_issue(ValidationLevel.ERROR,
                              "Вероятность ошибки должна быть в диапазоне 0.0-1.0",
                              'Employee', emp_id,
                              'emp_error_prob', employee.emp_error_prob)

        if hasattr(employee, 'emp_cost_per_hour'):
            if not isinstance(employee.emp_cost_per_hour, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Стоимость в час должна быть числом",
                              'Employee', emp_id,
                              'emp_cost_per_hour', employee.emp_cost_per_hour)
            elif employee.emp_cost_per_hour < 0:
                self._add_issue(ValidationLevel.WARNING,
                              "Стоимость в час отрицательная",
                              'Employee', emp_id,
                              'emp_cost_per_hour', employee.emp_cost_per_hour)

        if hasattr(employee, 'emp_efficiency'):
            if not isinstance(employee.emp_efficiency, dict):
                self._add_issue(ValidationLevel.ERROR,
                              "Эффективность должна быть словарём {навык: эффективность}",
                              'Employee', emp_id,
                              'emp_efficiency', type(employee.emp_efficiency))
            else:
                for skill, efficiency in employee.emp_efficiency.items():
                    if not isinstance(efficiency, (int, float)):
                        self._add_issue(ValidationLevel.ERROR,
                                      f"Эффективность навыка '{skill}' должна быть числом",
                                      'Employee', emp_id,
                                      f'emp_efficiency[{skill}]', efficiency)
                    elif not 0.0 <= efficiency <= 10.0:
                        self._add_issue(ValidationLevel.ERROR,
                                      f"Эффективность навыка '{skill}' должна быть в диапазоне 0.0-10.0",
                                      'Employee', emp_id,
                                      f'emp_efficiency[{skill}]', efficiency)

        if hasattr(employee, 'emp_max_daily_hours'):
            if not isinstance(employee.emp_max_daily_hours, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Максимальная дневная нагрузка должна быть числом",
                              'Employee', emp_id,
                              'emp_max_daily_hours', employee.emp_max_daily_hours)
            elif employee.emp_max_daily_hours <= 0:
                self._add_issue(ValidationLevel.ERROR,
                              "Максимальная дневная нагрузка должна быть положительной",
                              'Employee', emp_id,
                              'emp_max_daily_hours', employee.emp_max_daily_hours)
            elif employee.emp_max_daily_hours > 24:
                self._add_issue(ValidationLevel.WARNING,
                              "Максимальная дневная нагрузка превышает 24 часа в день",
                              'Employee', emp_id,
                              'emp_max_daily_hours', employee.emp_max_daily_hours)

        if hasattr(employee, 'emp_current_load'):
            if not isinstance(employee.emp_current_load, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Текущая нагрузка должна быть числом",
                              'Employee', emp_id,
                              'emp_current_load', employee.emp_current_load)
            elif employee.emp_current_load < 0:
                self._add_issue(ValidationLevel.WARNING,
                              "Текущая нагрузка отрицательная",
                              'Employee', emp_id,
                              'emp_current_load', employee.emp_current_load)

            if hasattr(employee, 'emp_max_daily_hours'):
                if employee.emp_current_load > employee.emp_max_daily_hours:
                    self._add_issue(ValidationLevel.WARNING,
                                  f"Текущая нагрузка ({employee.emp_current_load}) превышает максимальную ({employee.emp_max_daily_hours})",
                                  'Employee', emp_id,
                                  'emp_current_load', employee.emp_current_load)

        if hasattr(employee, 'emp_fatigue'):
            if not isinstance(employee.emp_fatigue, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Множитель усталости должен быть числом",
                              'Employee', emp_id,
                              'emp_fatigue', employee.emp_fatigue)
            elif employee.emp_fatigue <= 0:
                self._add_issue(ValidationLevel.WARNING,
                              "Множитель усталости неположительный",
                              'Employee', emp_id,
                              'emp_fatigue', employee.emp_fatigue)

        if hasattr(employee, 'emp_assigned_tasks'):
            if not isinstance(employee.emp_assigned_tasks, list):
                self._add_issue(ValidationLevel.ERROR,
                              "Назначенные задачи должны быть списком",
                              'Employee', emp_id,
                              'emp_assigned_tasks', type(employee.emp_assigned_tasks))

    def _validate_all_tasks(self, project):
        """Проверка всех задач."""
        if not hasattr(project, 'proj_tasks'):
            return

        for task_id, task in project.proj_tasks.items():
            self._validate_task(task, task_id)

    def _validate_task(self, task, task_id):
        """Проверка одной задачи."""
        required_fields = ["task_name", "task_skills", "task_duration_dist"]
        for field in required_fields:
            if not hasattr(task, field):
                self._add_issue(ValidationLevel.ERROR,
                              f"Отсутствует поле {field} у задачи",
                              'Task', task_id, field)

        if hasattr(task, 'task_name'):
            if not task.task_name:
                self._add_issue(ValidationLevel.ERROR,
                              "Название задачи отсутствует",
                              'Task', task_id,
                              'task_name', task.task_name)
            elif not isinstance(task.task_name, str):
                self._add_issue(ValidationLevel.ERROR,
                              "Название задачи должно быть строкой",
                              'Task', task_id,
                              'task_name', type(task.task_name))
            elif not task.task_name.strip():
                self._add_issue(ValidationLevel.ERROR,
                              "Название задачи состоит только из пробелов",
                              'Task', task_id,
                              'task_name', task.task_name)

        if hasattr(task, 'task_skills'):
            if not isinstance(task.task_skills, list):
                self._add_issue(ValidationLevel.ERROR,
                              "Требуемые навыки должны быть списком",
                              'Task', task_id,
                              'task_skills', type(task.task_skills))
            elif not task.task_skills:
                self._add_issue(ValidationLevel.WARNING,
                              "У задачи нет требуемых навыков",
                              'Task', task_id,
                              'task_skills', task.task_skills)
            else:
                for skill in task.task_skills:
                    if not isinstance(skill, str):
                        self._add_issue(ValidationLevel.ERROR,
                                      "Требуемый навык должен быть строкой",
                                      'Task', task_id,
                                      f'task_skills[{skill}]', type(skill))

        if hasattr(task, 'task_crit'):
            if not isinstance(task.task_crit, int):
                self._add_issue(ValidationLevel.ERROR,
                              "Критичность должна быть целым числом",
                              'Task', task_id,
                              'task_crit', task.task_crit)
            elif not 1 <= task.task_crit <= 5:
                self._add_issue(ValidationLevel.ERROR,
                              "Критичность должна быть в диапазоне от 1 до 5",
                              'Task', task_id,
                              'task_crit', task.task_crit)

        if hasattr(task, 'task_cost'):
            if not isinstance(task.task_cost, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Стоимость задачи должна быть числом",
                              'Task', task_id,
                              'task_cost', task.task_cost)
            elif task.task_cost < 0:
                self._add_issue(ValidationLevel.WARNING,
                              "Стоимость задачи отрицательная",
                              'Task', task_id,
                              'task_cost', task.task_cost)

        if hasattr(task, 'task_duration_dist'):
            if not isinstance(task.task_duration_dist, (list, tuple)):
                self._add_issue(ValidationLevel.ERROR,
                              "task_duration_dist должен быть списком или кортежем",
                              'Task', task_id,
                              'task_duration_dist', task.task_duration_dist)
            elif len(task.task_duration_dist) != 3:
                self._add_issue(ValidationLevel.ERROR,
                              f"task_duration_dist должен содержать 3 элемента (получено {len(task.task_duration_dist)})",
                              'Task', task_id,
                              'task_duration_dist', task.task_duration_dist)
            else:
                if not all(isinstance(x, (int, float)) for x in task.task_duration_dist):
                    self._add_issue(ValidationLevel.ERROR,
                                  "Все значения длительности должны быть числами",
                                  'Task', task_id,
                                  'task_duration_dist', task.task_duration_dist)
                else:
                    if not (task.task_duration_dist[0] <= task.task_duration_dist[1] <= task.task_duration_dist[2]):
                        self._add_issue(ValidationLevel.ERROR,
                                      f"Длительности должны быть в порядке: оптимистичная ≤ вероятная ≤ пессимистичная (получено {task.task_duration_dist})",
                                      'Task', task_id,
                                      'task_duration_dist', task.task_duration_dist)
                    if any(x <= 0 for x in task.task_duration_dist):
                        self._add_issue(ValidationLevel.ERROR,
                                      "Длительность должна быть положительной",
                                      'Task', task_id,
                                      'task_duration_dist', task.task_duration_dist)

        if hasattr(task, 'task_assigned_to'):
            if not isinstance(task.task_assigned_to, list):
                self._add_issue(ValidationLevel.ERROR,
                              "task_assigned_to должен быть списком",
                              'Task', task_id,
                              'task_assigned_to', task.task_assigned_to)
            else:
                for emp_id in task.task_assigned_to:
                    if not isinstance(emp_id, (int, str)):
                        self._add_issue(ValidationLevel.ERROR,
                                      f"ID назначенного сотрудника должен быть строкой или целым числом: {emp_id}",
                                      'Task', task_id,
                                      'task_assigned_to', emp_id)

        if hasattr(task, 'task_status'):
            valid_statuses = ['not_started', 'in_progress', 'completed', 'blocked']
            if task.task_status not in valid_statuses:
                self._add_issue(ValidationLevel.WARNING,
                              f"Неизвестный статус задачи: {task.task_status}",
                              'Task', task_id,
                              'task_status', task.task_status)

        if hasattr(task, 'task_actual_duration'):
            if task.task_actual_duration is not None:
                if not isinstance(task.task_actual_duration, (int, float)):
                    self._add_issue(ValidationLevel.ERROR,
                                  "Фактическая длительность должна быть числом",
                                  'Task', task_id,
                                  'task_actual_duration', task.task_actual_duration)
                elif task.task_actual_duration <= 0:
                    self._add_issue(ValidationLevel.WARNING,
                                  "Фактическая длительность неположительная",
                                  'Task', task_id,
                                  'task_actual_duration', task.task_actual_duration)

        if hasattr(task, 'task_primary_assignee'):
            if task.task_primary_assignee is not None:
                if not isinstance(task.task_primary_assignee, (int, str)):
                    self._add_issue(ValidationLevel.ERROR,
                                  "Основной исполнитель должен быть строкой или целым числом (ID)",
                                  'Task', task_id,
                                  'task_primary_assignee', task.task_primary_assignee)

    def _validate_dependencies(self, project):
        """Проверка всех зависимостей."""
        if not hasattr(project, 'proj_dependencies'):
            return

        if not project.proj_dependencies:
            return

        task_ids = set(project.proj_tasks.keys()) if project.proj_tasks else set()

        # Обработка как словаря (так и списка для обратной совместимости)
        if isinstance(project.proj_dependencies, dict):
            items = project.proj_dependencies.items()
        elif isinstance(project.proj_dependencies, list):
            items = enumerate(project.proj_dependencies)
        else:
            self._add_issue(ValidationLevel.ERROR,
                            "proj_dependencies должен быть списком или словарём",
                            'Project', 'project', 'proj_dependencies')
            return

        for dep_id, dependency in items:
            self._validate_dependency(dependency, dep_id, task_ids)

    def _validate_dependency(self, dependency, dep_id, task_ids):
        """Проверка одной зависимости."""
        if hasattr(dependency, 'dep_id') and dependency.dep_id is not None:
            if not isinstance(dependency.dep_id, int):
                self._add_issue(ValidationLevel.ERROR,
                              "ID зависимости должен быть целым числом",
                              'Dependency', dep_id,
                              'dep_id', dependency.dep_id)

        if not isinstance(dependency.dep_from_task, (int, str)):
            self._add_issue(ValidationLevel.ERROR,
                          "dep_from_task должен быть строкой или целым числом",
                          'Dependency', dep_id,
                          'dep_from_task', dependency.dep_from_task)
        elif dependency.dep_from_task not in task_ids:
            self._add_issue(ValidationLevel.ERROR,
                          f"Задача-предшественник {dependency.dep_from_task} не существует в проекте",
                          'Dependency', dep_id,
                          'dep_from_task', dependency.dep_from_task)

        if not isinstance(dependency.dep_to_task, (int, str)):
            self._add_issue(ValidationLevel.ERROR,
                          "dep_to_task должен быть строкой или целым числом",
                          'Dependency', dep_id,
                          'dep_to_task', dependency.dep_to_task)
        elif dependency.dep_to_task not in task_ids:
            self._add_issue(ValidationLevel.ERROR,
                          f"Задача-последователь {dependency.dep_to_task} не существует в проекте",
                          'Dependency', dep_id,
                          'dep_to_task', dependency.dep_to_task)

        if dependency.dep_from_task == dependency.dep_to_task:
            self._add_issue(ValidationLevel.ERROR,
                          "Задача не может зависеть от самой себя",
                          'Dependency', dep_id)

        valid_dep_types = ["FS", "SS", "FF", "SF"]
        if dependency.dep_type not in valid_dep_types:
            self._add_issue(ValidationLevel.ERROR,
                          f"Неизвестный тип зависимости: {dependency.dep_type}",
                          'Dependency', dep_id,
                          'dep_type', dependency.dep_type)

        if not isinstance(dependency.dep_lag, (int, float)):
            self._add_issue(ValidationLevel.ERROR,
                          "Lag должен быть числом",
                          'Dependency', dep_id,
                          'dep_lag', dependency.dep_lag)
        elif dependency.dep_lag < 0:
            self._add_issue(ValidationLevel.WARNING,
                          f"Отрицательный lag ({dependency.dep_lag}) может вызвать проблемы",
                          'Dependency', dep_id,
                          'dep_lag', dependency.dep_lag)

        if not isinstance(dependency.dep_mandatory, bool):
            self._add_issue(ValidationLevel.ERROR,
                          "dep_mandatory должен быть булевым значением",
                          'Dependency', dep_id,
                          'dep_mandatory', dependency.dep_mandatory)

    def _validate_outsources(self, project):
        """Проверка аутсорсинговых опций."""
        if not hasattr(project, 'proj_outsources'):
            return
        if not project.proj_outsources:
            return

        for i, outsource in enumerate(project.proj_outsources):
            self._validate_outsource(outsource, i)

    def _validate_outsource(self, outsource, outs_id):
        """Проверка одной аутсорсинговой опции."""
        if not hasattr(outsource, 'outs_id'):
            self._add_issue(ValidationLevel.ERROR,
                          "У аутсорсера нет ID",
                          'Outsource', outs_id)
        elif not isinstance(outsource.outs_id, int):
            self._add_issue(ValidationLevel.ERROR,
                          "ID аутсорсера должен быть целым числом",
                          'Outsource', outs_id,
                          'outs_id', outsource.outs_id)

        if not hasattr(outsource, 'outs_name'):
            self._add_issue(ValidationLevel.ERROR,
                          "У аутсорсера нет имени",
                          'Outsource', outs_id,
                          'outs_name')
        elif not outsource.outs_name or not isinstance(outsource.outs_name, str):
            self._add_issue(ValidationLevel.ERROR,
                          "Имя аутсорсера должно быть непустой строкой",
                          'Outsource', outs_id,
                          'outs_name', outsource.outs_name)

        if hasattr(outsource, 'outs_skills'):
            if not isinstance(outsource.outs_skills, list):
                self._add_issue(ValidationLevel.ERROR,
                              "Навыки аутсорсера должны быть списком",
                              'Outsource', outs_id,
                              'outs_skills', type(outsource.outs_skills))

        if hasattr(outsource, 'outs_daily_cost'):
            if not isinstance(outsource.outs_daily_cost, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Дневная стоимость должна быть числом",
                              'Outsource', outs_id,
                              'outs_daily_cost', outsource.outs_daily_cost)
            elif outsource.outs_daily_cost < 0:
                self._add_issue(ValidationLevel.WARNING,
                              "Дневная стоимость отрицательная",
                              'Outsource', outs_id,
                              'outs_daily_cost', outsource.outs_daily_cost)

        if hasattr(outsource, 'outs_reliability'):
            if not isinstance(outsource.outs_reliability, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Надёжность должна быть числом",
                              'Outsource', outs_id,
                              'outs_reliability', outsource.outs_reliability)
            elif not 0.0 <= outsource.outs_reliability <= 1.0:
                self._add_issue(ValidationLevel.ERROR,
                              "Надёжность должна быть в диапазоне 0.0-1.0",
                              'Outsource', outs_id,
                              'outs_reliability', outsource.outs_reliability)

        if hasattr(outsource, 'outs_lead_time_days'):
            if not isinstance(outsource.outs_lead_time_days, int):
                self._add_issue(ValidationLevel.ERROR,
                              "Время поставки должно быть целым числом дней",
                              'Outsource', outs_id,
                              'outs_lead_time_days', outsource.outs_lead_time_days)
            elif outsource.outs_lead_time_days < 0:
                self._add_issue(ValidationLevel.WARNING,
                              "Время поставки отрицательное",
                              'Outsource', outs_id,
                              'outs_lead_time_days', outsource.outs_lead_time_days)

        if hasattr(outsource, 'outs_duration_multiplier'):
            if not isinstance(outsource.outs_duration_multiplier, (int, float)):
                self._add_issue(ValidationLevel.ERROR,
                              "Множитель длительности должен быть числом",
                              'Outsource', outs_id,
                              'outs_duration_multiplier', outsource.outs_duration_multiplier)
            elif outsource.outs_duration_multiplier <= 0:
                self._add_issue(ValidationLevel.ERROR,
                              "Множитель длительности должен быть положительным",
                              'Outsource', outs_id,
                              'outs_duration_multiplier', outsource.outs_duration_multiplier)
            elif outsource.outs_duration_multiplier < 1.0:
                self._add_issue(ValidationLevel.WARNING,
                              "Множитель длительности меньше 1.0 (аутсорсер быстрее внутренней команды)",
                              'Outsource', outs_id,
                              'outs_duration_multiplier', outsource.outs_duration_multiplier)

    def _create_report(self) -> dict:
        """Формирует итоговый отчёт валидации."""
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
        """Печатает отчёт о валидации в удобочитаемом формате."""
        print("=" * 60)
        print("РЕЗУЛЬТАТЫ ВАЛИДАЦИИ ПРОЕКТА")
        print("=" * 60)

        if report["is_valid"]:
            print("✓ Проект валиден")
        else:
            print(f"✗ Найдено ошибок: {report['errors']}")

        print(f"  Предупреждений: {report['warnings']}")
        print(f"  Информационных сообщений: {report['infos']}")
        print(f"  Всего проблем: {report['total_issues']}")

        if report["issues_by_type"]:
            print("\nРаспределение проблем по типам объектов:")
            for obj_type, count in report["issues_by_type"].items():
                if count > 0:
                    print(f"  {obj_type}: {count}")

        if report["summary"]["errors"]:
            print("\nОШИБКИ (нужно исправить):")
            for i, error in enumerate(report["summary"]["errors"], 1):
                print(f"  {i}. {error}")

        if report["summary"]["warnings"]:
            print("\nПРЕДУПРЕЖДЕНИЯ (рекомендуется исправить):")
            for i, warning in enumerate(report["summary"]["warnings"], 1):
                print(f"  {i}. {warning}")

        print("=" * 60)
