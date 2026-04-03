"""
Test data generator for LTRROE system demonstration and validation
Provides comprehensive project data with realistic dependencies and assignments
"""

from models import Employee, Task, Dependency, Project, Outsource
from datetime import datetime, timedelta

def create_test_project():
    """Create a complete test project with 5 employees and 10 fully configured tasks"""
    project = Project()
    project.proj_start_date = datetime(2026, 1, 3)  # Fixed start date for reproducibility
    
    # 1. CREATE 5 EMPLOYEES WITH REALISTIC PROFILES
    
    senior = Employee(
        emp_id=0,
        emp_name="Alexey Seniorov",
        emp_skills=["architecture", "Python", "ML", "DevOps"],
        emp_error_prob=0.10,
        emp_cost_per_hour=50.0,
        emp_efficiency={"architecture": 1.3, "Python": 1.2, "ML": 1.2, "DevOps": 1.1}
    )
    
    mid1 = Employee(
        emp_id=1,
        emp_name="Maria Middlova",
        emp_skills=["Python", "UI/UX", "testing", "databases"],
        emp_error_prob=0.15,
        emp_cost_per_hour=35.0,
        emp_efficiency={"Python": 1.0, "UI/UX": 1.1, "testing": 0.9, "databases": 0.8}
    )
    
    mid2 = Employee(
        emp_id=2,
        emp_name="Ivan Middlov",
        emp_skills=["DevOps", "Python", "databases", "testing"],
        emp_error_prob=0.12,
        emp_cost_per_hour=32.0,
        emp_efficiency={"DevOps": 1.1, "Python": 0.9, "databases": 1.0, "testing": 0.8}
    )
    
    junior1 = Employee(
        emp_id=3,
        emp_name="Olga Juniorova",
        emp_skills=["Python", "testing", "documentation"],
        emp_error_prob=0.25,
        emp_cost_per_hour=20.0,
        emp_efficiency={"Python": 0.7, "testing": 0.8, "documentation": 0.9}
    )
    
    junior2 = Employee(
        emp_id=4,
        emp_name="Dmitry Juniorov",
        emp_skills=["UI/UX", "documentation", "Python"],
        emp_error_prob=0.30,
        emp_cost_per_hour=18.0,
        emp_efficiency={"UI/UX": 0.7, "documentation": 1.0, "Python": 0.6}
    )
    
    # Add all employees to project
    for emp in [senior, mid1, mid2, junior1, junior2]:
        project.proj_employees[emp.emp_id] = emp
    
    # 2. CREATE 10 TASKS WITH COMPLETE CONFIGURATION
    
    tasks = [
        Task(0, "System Architecture Design", ["architecture"], 5, 1000.0, (3, 5, 8)),
        Task(1, "Technical Documentation", ["documentation"], 1, 200.0, (2, 3, 5)),
        Task(2, "ML Model Development", ["Python", "ML"], 4, 800.0, (7, 10, 14)),
        Task(3, "UI/UX Design Implementation", ["UI/UX", "Python"], 3, 600.0, (5, 7, 10)),
        Task(4, "DevOps Infrastructure Setup", ["DevOps", "Python"], 4, 700.0, (4, 6, 9)),
        Task(5, "External API Integration", ["Python", "databases"], 3, 500.0, (3, 4, 6)),
        Task(6, "System Testing Suite", ["testing", "Python"], 4, 400.0, (4, 5, 7)),
        Task(7, "Performance Optimization", ["architecture", "Python"], 3, 600.0, (3, 4, 6)),
        Task(8, "Production Deployment", ["DevOps", "testing"], 5, 900.0, (2, 3, 5)),
        Task(9, "Final Build and Release", ["architecture", "DevOps"], 5, 1000.0, (3, 4, 6))
    ]
    
    for task in tasks:
        project.proj_tasks[task.task_id] = task
    
    # 3. CREATE REALISTIC DEPENDENCIES
    
    dependencies = [
        # Architecture is foundation for everything
        Dependency(0, 2, "FS", 0.0, True),  # Architecture → ML
        Dependency(0, 3, "FS", 0.0, True),  # Architecture → UI/UX
        Dependency(0, 4, "FS", 0.0, True),  # Architecture → DevOps
        Dependency(0, 5, "FS", 0.0, True),  # Architecture → API
        Dependency(0, 6, "FS", 0.0, True),  # Architecture → Testing
        Dependency(0, 7, "FS", 0.0, True),  # Architecture → Optimization
        Dependency(0, 8, "FS", 0.0, True),  # Architecture → Deployment
        Dependency(0, 9, "FS", 0.0, True),  # Architecture → Final
        
        # Development flow
        Dependency(2, 6, "FS", 2.0, True),   # ML → Testing (after 2 days)
        Dependency(3, 6, "SS", 1.0, True),   # UI/UX → Testing (start together)
        Dependency(4, 8, "FS", 1.0, True),   # DevOps → Deployment
        Dependency(6, 8, "FS", 0.0, True),   # Testing → Deployment
        Dependency(8, 9, "FS", 0.0, True),   # Deployment → Final
        
        # Documentation can start anytime
        Dependency(0, 1, "SS", 0.0, False),  # Architecture → Docs (optional)
    ]
    
    project.proj_dependencies = dependencies
    
    # 4. ASSIGN TASKS WITH REALISTIC WORKLOADS
    
    # Task 0: Architecture → Senior (6h/day)
    senior.emp_assigned_tasks.append(0)
    senior.emp_current_load += 6.0
    tasks[0].task_assigned_to.append(0)
    
    # Task 1: Documentation → Junior2 (4h/day)
    junior2.emp_assigned_tasks.append(1)
    junior2.emp_current_load += 4.0
    tasks[1].task_assigned_to.append(4)
    
    # Task 2: ML → Senior (4h/day)
    senior.emp_assigned_tasks.append(2)
    senior.emp_current_load += 4.0
    tasks[2].task_assigned_to.append(0)
    
    # Task 3: UI/UX → Junior2 (3h) + Mid1 (3h)
    junior2.emp_assigned_tasks.append(3)
    mid1.emp_assigned_tasks.append(3)
    junior2.emp_current_load += 3.0
    mid1.emp_current_load += 3.0
    tasks[3].task_assigned_to.extend([4, 1])
    
    # Task 4: DevOps → Mid2 (5h/day)
    mid2.emp_assigned_tasks.append(4)
    mid2.emp_current_load += 5.0
    tasks[4].task_assigned_to.append(2)
    
    # Task 5: API → Mid1 (4h/day)
    mid1.emp_assigned_tasks.append(5)
    mid1.emp_current_load += 4.0
    tasks[5].task_assigned_to.append(1)
    
    # Task 6: Testing → Junior1 (4h) + Mid1 (2h)
    junior1.emp_assigned_tasks.append(6)
    mid1.emp_assigned_tasks.append(6)
    junior1.emp_current_load += 4.0
    mid1.emp_current_load += 2.0
    tasks[6].task_assigned_to.extend([3, 1])
    
    # Task 7: Optimization → Senior (3h/day)
    senior.emp_assigned_tasks.append(7)
    senior.emp_current_load += 3.0
    tasks[7].task_assigned_to.append(0)
    
    # Task 8: Deployment → Mid2 (3h) + Junior1 (3h)
    mid2.emp_assigned_tasks.append(8)
    junior1.emp_assigned_tasks.append(8)
    mid2.emp_current_load += 3.0
    junior1.emp_current_load += 3.0
    tasks[8].task_assigned_to.extend([2, 3])
    
    # Task 9: Final → Senior (4h) + Mid2 (4h)
    senior.emp_assigned_tasks.append(9)
    mid2.emp_assigned_tasks.append(9)
    senior.emp_current_load += 4.0
    mid2.emp_current_load += 4.0
    tasks[9].task_assigned_to.extend([0, 2])
    
    # 5. CREATE OUTSOURCING OPTIONS
    
    project.proj_outsources = [
        Outsource(0, "Upwork DevOps Expert", ["DevOps", "Python", "databases"], 
                  500.0, 0.8, 5, 1.3),
        Outsource(1, "Freelance UI/UX Designer", ["UI/UX", "Python"], 
                  400.0, 0.7, 3, 1.5)
    ]
    
    return project

def create_simple_project():
    """Create a minimal project for quick testing (3 tasks, 2 employees)"""
    project = Project()
    project.proj_start_date = datetime(2026, 1, 1)
    
    # Simple team
    alice = Employee(0, "Alice", ["Python", "testing"], 0.1, 40.0, {"Python": 1.0, "testing": 0.9})
    bob = Employee(1, "Bob", ["DevOps", "Python"], 0.15, 35.0, {"DevOps": 1.1, "Python": 0.8})
    
    project.proj_employees = {0: alice, 1: bob}
    
    # Simple tasks
    tasks = [
        Task(0, "Design", ["Python"], 3, 500.0, (2, 3, 5)),
        Task(1, "Implement", ["Python", "DevOps"], 4, 800.0, (4, 5, 7)),
        Task(2, "Test", ["testing"], 2, 300.0, (1, 2, 3))
    ]
    
    for task in tasks:
        project.proj_tasks[task.task_id] = task
    
    # Simple dependencies
    project.proj_dependencies = [
        Dependency(0, 1, "FS", 0.0, True),
        Dependency(1, 2, "FS", 1.0, True)
    ]
    
    # Assignments
    alice.emp_assigned_tasks = [0, 2]
    alice.emp_current_load = 5.0
    bob.emp_assigned_tasks = [1]
    bob.emp_current_load = 6.0
    
    tasks[0].task_assigned_to = [0]
    tasks[1].task_assigned_to = [1]
    tasks[2].task_assigned_to = [0]
    
    return project
