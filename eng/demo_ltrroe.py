"""
LTRROE Complete Demonstration
Academic Research Project in Stochastic Project Risk Modeling
Formal presentation for academic review
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from test_data import create_test_project
from algorithmes import calculate_schedule, monte_carlo_simulation, calculate_backward_pass
from visualisation import (
    plot_gantt_chart, 
    plot_monte_carlo_histogram, 
    plot_employee_load_heatmap, 
    plot_skills_radar_chart
)

def demonstrate_research_project():
    """Formal academic demonstration of LTRROE research capabilities"""
    print("\n" + "="*70)
    print("LTRROE v2.0 - STOCHASTIC PROJECT RISK ANALYSIS DEMONSTRATION")
    print("Research Project for Academic Review")
    print("="*70)
    
    # 1. Project instantiation
    print("\n1. PROJECT INSTANTIATION")
    print("   Creating stochastic project model with:")
    project = create_test_project()
    print(f"   - {len(project.proj_tasks)} tasks with triangular duration distributions")
    print(f"   - {len(project.proj_employees)} employees with skill efficiency profiles")
    print(f"   - {len(project.proj_dependencies)} task dependencies (DAG structure)")
    print(f"   - Project start: {project.proj_start_date.strftime('%Y-%m-%d')}")
    
    # 2. Deterministic schedule calculation
    print("\n2. DETERMINISTIC SCHEDULE ANALYSIS (CRITICAL PATH METHOD)")
    early_start, early_finish, task_duration = calculate_schedule(project)
    late_start, late_finish = calculate_backward_pass(project, early_finish, task_duration)
    
    critical_tasks = []
    for task_id in early_start:
        slack = (late_start[task_id] - early_start[task_id]).days
        if slack == 0:
            critical_tasks.append(task_id)
    
    project_end = max(early_finish.values())
    deterministic_duration = (project_end - project.proj_start_date).days
    print(f"   - Deterministic project duration: {deterministic_duration} days")
    print(f"   - Critical path tasks: {sorted(critical_tasks)}")
    print(f"   - Tasks with slack time: {len(project.proj_tasks) - len(critical_tasks)}")
    
    # 3. Monte Carlo analysis
    print("\n3. STOCHASTIC RISK ASSESSMENT (MONTE CARLO SIMULATION)")
    print("   Running 1000 stochastic simulations...")
    mc_durations = monte_carlo_simulation(project, num_simulations=1000)
    
    mc_mean = sum(mc_durations) / len(mc_durations)
    
    print(f"   - Monte Carlo mean duration: {mc_mean:.1f} days")
    print(f"   - Deterministic vs Stochastic difference: {mc_mean - deterministic_duration:.1f} days (+{(mc_mean/deterministic_duration-1)*100:.1f}%)")
    
    deadline = 30
    success = sum(1 for d in mc_durations if d <= deadline)
    risk_percentage = 100 - (success/len(mc_durations)*100)
    print(f"   - Probability of missing {deadline}-day deadline: {risk_percentage:.1f}%")
    
    # 4. Resource analysis
    print("\n4. RESOURCE UTILIZATION ANALYSIS")
    employees = list(project.proj_employees.values())
    overloaded = []
    for emp in employees:
        if emp.emp_current_load > emp.emp_max_daily_hours:
            overloaded.append(emp.emp_name)
    
    print(f"   - Team size: {len(employees)} members")
    print(f"   - Overloaded employees: {len(overloaded)} ({', '.join(overloaded) if overloaded else 'none'})")
    
    # 5. Skills analysis
    print("\n5. COMPETENCY GAP ANALYSIS")
    radar_data = plot_skills_radar_chart(project)
    if radar_data:
        print(f"   - Unique skills identified: {len(radar_data['skills'])}")
        print(f"   - Average team-proficiency gap: {radar_data['total_gap']:.1%}")
    
    # 6. Visualization
    print("\n6. VISUALIZATION REPORT GENERATION")
    print("   Creating analytical dashboards...")
    
    # Generate all visualizations
    gantt_result = plot_gantt_chart(project, early_start, early_finish, late_start)
    mc_result = plot_monte_carlo_histogram(mc_durations, deadline=deadline)
    heatmap_result = plot_employee_load_heatmap(project, early_start, early_finish)
    
    print(f"   - Gantt Chart: {'Generated' if gantt_result[0] else 'Failed'}")
    print(f"   - Monte Carlo Distribution: {'Generated' if mc_result[0] else 'Failed'}")
    print(f"   - Resource Heatmap: {'Generated' if heatmap_result[0] else 'Failed'}")
    print(f"   - Skills Radar Analysis: {'Generated' if radar_data else 'Failed'}")
    
    # 7. Summary
    print("\n" + "="*70)
    print("ACADEMIC RESEARCH SUMMARY")
    print("="*70)
    
    summary = """
METHODOLOGICAL CONTRIBUTIONS:
1. Formalization of project structure as Directed Acyclic Graph (DAG)
2. Integration of triangular probability distributions (PERT methodology)
3. Monte Carlo simulation for uncertainty quantification (N=1000)
4. Critical Path Method (CPM) with probabilistic extensions
5. Human factor modeling via skill-efficiency matrices
6. Multi-dimensional visualization for analytical decision support

RESEARCH SIGNIFICANCE:
- Transition from deterministic to probabilistic project planning
- Quantitative risk assessment for managerial decision-making
- Integration of human factors in computational models
- Scalable framework for complex project ecosystems

ACADEMIC ALIGNMENT:
The system demonstrates applications of:
- Probability Theory and Stochastic Processes
- Operations Research and Optimization
- Graph Theory and Network Analysis
- Data Visualization and Computational Methods
"""
    
    print(summary)
    
    print("\nGENERATED ANALYTICAL REPORTS:")
    print("- gantt_chart.png (Schedule visualization with critical path)")
    print("- monte_carlo_histogram.png (Probability distribution)")
    print("- employee_load_heatmap.png (Resource utilization)")
    print("- skills_radar_chart.png (Competency gap analysis)")
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE - READY FOR ACADEMIC REVIEW")
    print("="*70)

if __name__ == "__main__":
    demonstrate_research_project()
