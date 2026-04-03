from enum import Enum
from dataclasses import dataclass

# Уровни серьезности проблем
class ValidationLevel(Enum):
    ERROR = "ERROR"      # критично, нужно исправить
    WARNING = "WARNING"  # не критично, но странно
    INFO = "INFO"        # просто информация

# Структура для одной найденной проблемы
@dataclass
class ValidationIssue:
    level: ValidationLevel  # уровень (ERROR/WARNING/INFO)
    message: str           # сообщение что не так
    object_type: str       # 'Employee', 'Task', 'Project'
    object_id: Any         # ID объекта (emp_id, task_id)
    field: str = None      # какое поле проблемное
    value: Any = None      # какое значение

class LTRROEValidator:
    def __init__(self):
        self.issues = []  # здесь будут все найденные проблемы
    
    def validate_project(self, project) -> dict:
        """
        Главный метод: проверяет весь проект.
        
        Возвращает словарь с результатами.
        """
        self.issues.clear()  # очищаем старые результаты
        
        # Последовательно проверяем все части проекта
        self._check_project_basics(project)
        self._validate_all_employees(project)
        self._validate_all_tasks(project)  
        self._validate_dependencies(project)
        self._validate_assignments(project)
        
        # Формируем итоговый отчет
        return self._create_report()

    def _check_project_basics(self, project):
        """Проверка базовых компонентов проекта."""
        if not hasattr(project, 'proj_tasks') or not project.proj_tasks:
            self._add_issue(ValidationLevel.WARNING, "В проекте нет задач"), 'Project', 'project'
            
        if not hasattr(project, 'proj_tasks') or not project.proj_tasks:
            self._add_issue(ValidationLevel.WARNING, "В проекте нет задач"), 'Project', 'project'

        if hasattr(project, 'proj_start_date'):
            if not isinstance(project.proj_start_date, datetime):
                self._add_issue(ValidationLevel.WARNING, "Некорректная дата начала проекта"),
                'Project', 'project', 'proj_start_date', project.proj_start_date

    def _validate_all_employees(self, project):
        """Проверка всех сотрудников."""
        if not hasattr(project, 'proj_employees'):
            return

        for emp_id, employee in project.proj_employees.items():
            self._validate_employee(employee, emp_id)

    def _validate_employee(self, employee, emp_id):
        """Проверка одного сотрудника"""
        required_fields = ["emp_name", "emp_skills", "emp_max_daily_hours"]
        for field in required_fiels:
             if not hasattr(employee, field):
                 self._add_issue(ValidationLevel.ERROR, f"Отсутствуют поля {field} у сотрудников", 'Employee', emp_id, field)

        if hasattr(employee, 'emp_name'):
            if not employee.emp_name or not employee.emp_name.strip:
                self._add_issue(ValidationLevel.ERROR, "Имя отсутствует или состоит из пробелов",
                                'Employee', emp_id, 'emp_name', employee.emp_name)

        if hasattr(employee, 'emp_skills'):
            if not employee.emp_skills:
                self._add_issue(ValidationLevel.ERROR, "Отсутствуют указанные навыки у сотрудника",
                                'Employee', emp_id, 'emp_skills', employee.emp_name)

        if hasattr(employee, 'emp_max_daily_hours'):
            if not isinstance(employee, emp_max_daily_hours(int, float)):
                self._add_issue(ValidationLevel.ERROR, "Максимальная нагрузка должна быть числом",
                                'Employee', emp_id, 'emp_max_daily_hours', employee.emp_max_daily_hours)
                              
            elif employee_max_daily_hours <= 0:
                self._add_issue(ValidationLevel.ERROR, "Максимальная нагрузка должна быть положительным числом",
                                'Employee', emp_id, 'emp_max_daily_hours', employee.emp_max_daily_hours)

            elif employee_max_daily_hours > 24:
                self._add_issue(ValidationLevel.WARNING, "Максимальная нагрузка больше 24 часов в день",
                                'Employee', emp_id, 'emp_max_daily_hours', employee.emp_max_daily_hours)

        if hasattr(employee, 'emp_current_load'):
            if hasattr(employee, 'emp_max_daily_hours'):
                if employee_current_load > employee_max_daily_hours:
                    self._add_issue(ValidationLevel.WARNING, f"Текущая ({emp_current_load} нагрузка превышает максимальную ({emp_max_daily_hours})",
                                    'Employee', emp_id, 'emp_max_daily_hours', employee.emp_max_daily_hours)
                    
        if hasattr(employee, 'emp_efficiency'):
            if not isinstance(employee, emp_efficiency, dict):
                self._add_issue(ValidationLevel.ERROR, "Эффективность должна быть словарем {skill: efficiency}", 'Employee', emp_id, 'emp_efficiency', type(employee.emp_efficiency)
            else:
                for skill, efficiency in employee.emp_efficiency.items():
                    if not 0.0 <= efficiency <= 10000.0:
                        self._add_issue(ValidationLevel.ERROR, f"Эффективность навыка {skill} должна быть в диапазоне от 0.0 до 10000.0", 'Employee', emp_id, f'emp_efficiency[{skill}]', efficiency

    def _validate_all_task(self, project):
         if not hasattr(project, 'proj_tasks'):
            return

        for task_id, task in project.proj_task.items():
            self._validate_task(task, task_id)

    def _validate_task(self, task, task_id):
        """Проверка одной задачи"""
        required_fields = ["task_name", "task_skills", "task_duration_dist"]
        for field in required_fields:
             if not hasattr(task, field):
                 self._add_issue(ValidationLevel.ERROR, f"Отсутствуют поля {field} у задач", 'Task', task_id, field)

        if hasattr(task, 'task_name'):
            if not task.task_name or not task.task_name.strip():
                self._add_issue(ValidationLevel.ERROR, "Название отсутствует или состоит из пробелов",
                                'Task', task_id, 'task_name', task.task_name)

        if hasattr(task, 'task_skills'):
            if not task.task_skills:
                self._add_issue(ValidationLevel.WARNING, "Отсутствуют требуемые навыки у задачи",
                                'Task', task_id, 'task_skills', task.task_skills)

        if hasattr(task, 'task_crit'):
            if not isinstance(task, task_crit (int, float)):
                self._add_issue(ValidationLevel.ERROR, "Критичность должна быть числом",
                                'Task', task_id, 'task_crit', task.task_crit)
            elif not 1 <= task.task_crit <= 5:
                self._add_issue(ValidationLevel.ERROR, "Критичность должна быть в диапазоне от 0 до 5",
                                'Task', task_id, 'task_crit', task.task_crit)

        if not isinstance(task.task_duration_dist, (list, tuple)):
            self._add_issue(ValidationLevel.ERROR,
                          "task_duration_dist должен быть списком/кортежем",
                          'Task', task_id, 'task_duration_dist', task.task_duration_dist)
            
        elif len(task.task_duration_dist) != 3:
            self._add_issue(ValidationLevel.ERROR,
                          f"task_duration_dist должен иметь 3 элемента (получено {len(task.task_duration_dist)})",
                          'Task', task_id, 'task_duration_dist', task.task_duration_dist)
            
        else:
            if not all(isinstance(x(int, float)) for x in task.task_duration_dist:
                self._add_issue(ValidationLevel.ERROR, "Все значения длительности должны быть числами",
                              'Task', task_id, 'task_duration_dist', task.task_duration_dist)

        elif not (task.task_duration_dist[0] <= task.task_duration_dist[1] <= task.task_duration_dist[2]):
                self._add_issue(ValidationLevel.ERROR,
                              f"Длительности должны быть в порядке: optimistic ≤ likely ≤ pessimistic (получено {task.task_duration_dist})",
                              'Task', task_id, 'task_duration_dist', task.task_duration_dist)

        elif any(x <= 0 for x in task.task_duration_dist):
            self._add_issue(ValidationLevel.ERROR, "Длительность должна быть положительным числом", 'Task', task_id, 'task_duration_dist', task.task_duration_dist)
            
        if hasattr(task, 'task_assigned_to'):
            if not isinstance(task.task_assigned_to, list):
                self._add_issue(ValidationLevel.ERROR, "task_assigned_to должен быть списком", 'Task', task_id, 'task_assigned_to', task.task_assgined_to)

        if hasattr(task, 'task_status'):
            valid_statuses = ['not_started', 'in_progress', 'completed', 'blocked']
            if task.task_status not in valid_statuses:
                self._add_issue(ValidationLevel.WARNING, f"Неизвестный статус задачи {task.task_status}", 'Task', task_id, 'task_status', task.task_status)

    def _validate_all_dependencies(self, project):
        if not hasattr(project, 'proj_tasks'):
            return

                                
        
