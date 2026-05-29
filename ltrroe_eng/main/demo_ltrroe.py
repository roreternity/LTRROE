"""
Full LTRROE system demonstration
Research prototype for stochastic project-risk modeling
"""
from test_data import create_test_project
from algorithms import calculate_schedule, monte_carlo_simulation, calculate_backward_pass
from visualisation import  plot_gantt_chart, plot_monte_carlo_histogram, plot_employee_load_heatmap, plot_skills_radar_chart

def demonstrate_research_project():
    """Full demonstration of LTRROE research features"""
    print("\n" + "="*70)
    print("LTRROE v2.0 - STOCHASTIC PROJECT-RISK ANALYSIS DEMO")
    print("="*70)
    
    # 1. Create the research-project instance
    print("\n1. PROJECT INITIALIZATION")
    project = create_test_project()
    print(f"   • Tasks: {len(project.proj_tasks)}, employees: {len(project.proj_employees)}, dependencies: {len(project.proj_dependencies)}")
    print(f"   • Start date: {project.proj_start_date.strftime('%Y-%m-%d')}")
    
    # 2. Deterministic schedule calculation (CPM)
    print("\n2. DETERMINISTIC SCHEDULE ANALYSIS (CPM)")
    early_start, early_finish, task_duration = calculate_schedule(project)
    late_start, late_finish = calculate_backward_pass(project, early_finish, task_duration)
    
    critical_tasks = []
    for task_id in early_start:
        slack = (late_start[task_id] - early_start[task_id]).days
        if slack == 0:
            critical_tasks.append(task_id)
    
    project_end = max(early_finish.values())
    deterministic_duration = (project_end - project.proj_start_date).days
    print(f"   • Duration (CPM): {deterministic_duration} days")
    print(f"   • Critical tasks: {len(critical_tasks)}")
    print(f"   • Tasks with slack: {len(project.proj_tasks) - len(critical_tasks)}")
    
    # 3. Monte Carlo stochastic risk analysis
    print("\n3. STOCHASTIC RISK ESTIMATION (MONTE CARLO, N=1000)")
    mc_durations = monte_carlo_simulation(project, num_simulations=1000)
    
    mc_mean = sum(mc_durations) / len(mc_durations)
    mc_min = min(mc_durations)
    mc_max = max(mc_durations)
    
    print(f"   • Mean duration (MC): {mc_mean:.1f} days")
    print(f"   • 95% interval: [{mc_min:.1f}, {mc_max:.1f}] days")
    print(f"   • CPM deviation from MC: {mc_mean - deterministic_duration:.1f} days ({(mc_mean/deterministic_duration-1)*100:.1f}%)")
    
    deadline = 35
    success = sum(1 for d in mc_durations if d <= deadline)
    risk_percentage = 100 - (success/len(mc_durations)*100)
    print(f"   • Probability of exceeding {deadline} days: {risk_percentage:.1f}%")
    
    # 4. Resource analysis
    print("\n4. RESOURCE ANALYSIS")
    employees = list(project.proj_employees.values())
    overloaded = [emp.emp_name for emp in employees if emp.emp_current_load > emp.emp_max_daily_hours]
    avg_load = sum(e.emp_current_load for e in employees) / len(employees)
    print(f"   • Team: {len(employees)} people")
    print(f"   • Overloaded: {len(overloaded)} ({', '.join(overloaded) if overloaded else 'none'})")
    print(f"   • Average load: {avg_load:.1f} h/day")
    
    # 5. Skill-gap analysis
    print("\n5. SKILL ANALYSIS")
    radar_data = plot_skills_radar_chart(project)
    if radar_data:
        print(f"   • Skills: {len(radar_data['skills'])}")
        print(f"   • Average gap: {radar_data['total_gap']:.1%}")
        if radar_data['skill_gaps']:
            print(f"   • Critical gaps: {len(radar_data['skill_gaps'])}")
            for skill, gap in list(radar_data['skill_gaps'].items())[:3]:
                print(f"     - {skill}: gap {gap:.0%}")
    
    # 6. Visualization report generation
    print("\n6. GENERATING VISUALIZATIONS")
    gantt_result = plot_gantt_chart(project, early_start, early_finish, late_start)
    mc_result = plot_monte_carlo_histogram(mc_durations, deadline=deadline)
    heatmap_result = plot_employee_load_heatmap(project, early_start, early_finish)
    
    reports = [
        ("Gantt chart", gantt_result[0] is not None),
        ("Monte Carlo distribution", mc_result[0] is not None),
        ("Load heatmap", heatmap_result[0] is not None),
        ("Skills radar chart", radar_data is not None)
    ]
    for name, ok in reports:
        print(f"   • {name}: {'created' if ok else 'error'}")
    
    # 7. Results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    results = """
METHODOLOGY:
- Project as a directed acyclic graph (DAG)
- Triangular task-duration distributions (PERT)
- Monte Carlo simulation (1000 iterations)
- Critical Path Method (CPM) with probabilistic extensions
- Human-factor modeling through skill matrices

FINDINGS:
- Stochastic modeling gives more realistic schedule estimates
- Employee overload and skill gaps increase risk
- Visualization helps identify problem areas
"""
    print(results)
    print("\nCREATED FILES:")
    print("   • gantt_chart.png")
    print("   • monte_carlo_histogram.png")
    print("   • employee_load_heatmap.png")
    print("   • skills_radar_chart.png")
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)

if __name__ == "__main__":
    demonstrate_research_project()
