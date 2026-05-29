"""
LTRROE test-data generator
Creates a complete test project for demonstration and validation
"""

from ltrroe_objects import Employee, Task, Dependency, Project, Outsource
from datetime import datetime

def create_test_project():
    """Create a complete test project with 5 employees and 10 tasks"""
    project = Project(proj_id="pilot_demo")
    project.proj_start_date = datetime(2026, 1, 3)  # Fixed start date
    
    # 1. CREATE 5 EMPLOYEES
    # 1 SENIOR - lead developer
    senior = Employee(
        emp_id=0,
        emp_name="Alex Senior",
        emp_skills=["architecture", "Python", "ML", "DevOps"],
        emp_error_prob=0.10,
        emp_cost_per_hour=50.0,
        emp_efficiency={
            "architecture": 1.3,
            "Python": 1.2,
            "ML": 1.2,
            "DevOps": 1.1
        }
    )
    
    # 2 MIDDLE 1
    mid1 = Employee(
        emp_id=1,
        emp_name="Maria Middle",
        emp_skills=["Python", "UI/UX", "testing", "databases"],
        emp_error_prob=0.15,
        emp_cost_per_hour=35.0,
        emp_efficiency={
            "Python": 1.0,
            "UI/UX": 1.1,
            "testing": 0.9,
            "databases": 0.8
        }
    )
    
    # 3 MIDDLE 2
    mid2 = Employee(
        emp_id=2,
        emp_name="Ivan Middle",
        emp_skills=["DevOps", "Python", "databases", "testing"],
        emp_error_prob=0.12,
        emp_cost_per_hour=32.0,
        emp_efficiency={
            "DevOps": 1.1,
            "Python": 0.9,
            "databases": 1.0,
            "testing": 0.8
        }
    )
    
    # 4 JUNIOR 1
    junior1 = Employee(
        emp_id=3,
        emp_name="Olga Junior",
        emp_skills=["Python", "testing", "documentation"],
        emp_error_prob=0.25,
        emp_cost_per_hour=20.0,
        emp_efficiency={
            "Python": 0.7,
            "testing": 0.8,
            "documentation": 0.9
        }
    )
    
    # 5 JUNIOR 2
    junior2 = Employee(
        emp_id=4,
        emp_name="Dmitry Junior",
        emp_skills=["UI/UX", "documentation", "Python"],
        emp_error_prob=0.30,
        emp_cost_per_hour=18.0,
        emp_efficiency={
            "UI/UX": 0.7,
            "documentation": 1.0,
            "Python": 0.6
        }
    )
    
    # Add employees to the project
    employees = [senior, mid1, mid2, junior1, junior2]
    for emp in employees:
        project.proj_employees[emp.emp_id] = emp
    
    # 2. CREATE 10 TASKS
    
    tasks = [
        Task(0, "System architecture design", ["architecture"], 5, 1000.0, (3, 5, 8)),
        Task(1, "Technical documentation", ["documentation"], 1, 200.0, (2, 3, 5)),
        Task(2, "ML model development", ["Python", "ML"], 4, 800.0, (7, 10, 14)),
        Task(3, "UI/UX implementation", ["UI/UX", "Python"], 3, 600.0, (5, 7, 10)),
        Task(4, "DevOps infrastructure setup", ["DevOps", "Python"], 4, 700.0, (4, 6, 9)),
        Task(5, "External API integration", ["Python", "databases"], 3, 500.0, (3, 4, 6)),
        Task(6, "System integration testing", ["testing", "Python"], 4, 400.0, (4, 5, 7)),
        Task(7, "Performance optimization", ["architecture", "Python"], 3, 600.0, (3, 4, 6)),
        Task(8, "Production deployment", ["DevOps", "testing"], 5, 900.0, (2, 3, 5)),
        Task(9, "Final build and release", ["architecture", "DevOps"], 5, 1000.0, (3, 4, 6))
    ]
    
    for task in tasks:
        project.proj_tasks[task.task_id] = task
    
    # 3. CREATE DEPENDENCIES
    
    dependencies = [
        # Architecture is the foundation for the project
        Dependency(0, 2, "FS", 0.0, True),  # Architecture → ML
        Dependency(0, 3, "FS", 0.0, True),  # Architecture → UI/UX
        Dependency(0, 4, "FS", 0.0, True),  # Architecture → DevOps
        Dependency(0, 5, "FS", 0.0, True),  # Architecture → API
        Dependency(0, 6, "FS", 0.0, True),  # Architecture → Testing
        Dependency(0, 7, "FS", 0.0, True),  # Architecture → Optimization
        Dependency(0, 8, "FS", 0.0, True),  # Architecture → Deploy
        Dependency(0, 9, "FS", 0.0, True),  # Architecture → Final
        
        # Additional dependencies
        Dependency(2, 6, "FS", 2.0, True),   # ML → Testing (after 2 days)
        Dependency(3, 6, "SS", 1.0, True),   # UI/UX → Testing (start together)
        Dependency(4, 8, "FS", 1.0, True),   # DevOps → Deploy
        Dependency(6, 8, "FS", 0.0, True),   # Testing → Deploy
        Dependency(8, 9, "FS", 0.0, True),   # Deploy → Final
        
        # Documentation can start at any time
        Dependency(0, 1, "SS", 0.0, False),  # Architecture → Documentation (optional)
    ]
    
    project.proj_dependencies = dependencies
    
    # 4. ASSIGN TASKS
    
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
    
    # Task 8: Deploy → Mid2 (3h) + Junior1 (3h)
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
    
    # 5. CREATE OUTSOURCE OPTIONS
    
    project.proj_outsources = [
        Outsource(0, "Upwork DevOps Expert", ["DevOps", "Python", "databases"], 
                  500.0, 0.8, 5, 1.3),
        Outsource(1, "Freelance UI/UX Designer", ["UI/UX", "Python"], 
                  400.0, 0.7, 3, 1.5)
    ]
    
    return project
