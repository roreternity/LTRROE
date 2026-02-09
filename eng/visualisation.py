"""
LTRROE Visualization Module
Generate charts and diagrams based on simulation analysis results

Core Functions:
- plot_gantt_chart() - Gantt chart with criticality color coding
- plot_monte_carlo_histogram() - Simulation result distribution with confidence intervals
- plot_employee_load_heatmap() - Team workload heatmap with overload highlights
- plot_skills_radar_chart() - Skills gap analysis radar chart
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from math import pi
from typing import Dict, List, Tuple, Optional, Any

def plot_gantt_chart(project, early_start: Dict, early_finish: Dict, 
                     late_start: Optional[Dict] = None) -> Tuple[Optional[plt.Figure], Optional[plt.Axes]]:
    """
    Generate Gantt chart displaying tasks as horizontal bars
    Returns: (figure, axes) tuple or (None, None) on error
    """
    try: 
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Sort tasks by start date
        sorted_tasks = sorted(early_start.items(), key=lambda x: x[1])
    
        # Criticality-based color scheme
        colors = ['#FF6B6B', '#FFA726', '#FFD166', '#06D6A0', '#118AB2']
        
        y_positions = []
        task_labels = []
        
        for i, (task_id, start_date) in enumerate(sorted_tasks):
            task = project.proj_tasks[task_id]
            
            # Convert dates to matplotlib numeric format
            start_num = mdates.date2num(start_date)
            end_date = early_finish[task_id]
            end_num = mdates.date2num(end_date)
            duration_days = (end_date - start_date).days
            
            # Determine color based on criticality (1-5)
            color_index = min(task.task_crit - 1, 4) if 1 <= task.task_crit <= 5 else 0
            
            # Draw task bar
            ax.barh(
                y=i,
                width=duration_days,
                left=start_num,
                height=0.6,
                color=colors[color_index],
                edgecolor='black',
                linewidth=1
            )
            
            # Add task label inside bar
            mid_point = start_num + duration_days / 2
            short_name = task.task_name[:15] + "..." if len(task.task_name) > 15 else task.task_name
            
            ax.text(
                mid_point, i,
                f"{task_id}: {short_name}",
                va='center',
                ha='center',
                fontsize=9,
                color='white',
                fontweight='bold'
            )
            
            y_positions.append(i)
            task_labels.append(f"Task {task_id}")
        
        # Configure axes
        ax.set_yticks(y_positions)
        ax.set_yticklabels(task_labels)
        
        # Format date axis
        ax.xaxis_date() 
        date_fmt = mdates.DateFormatter('%d.%m')
        ax.xaxis.set_major_formatter(date_fmt)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=45)
        
        # Labels and title
        ax.set_xlabel('Date')
        ax.set_title('Project Gantt Chart')
        ax.grid(True, alpha=0.3, linestyle='--', which='both')
        
        # Legend
        legend_patches = []
        for i, color in enumerate(colors):
            crit_level = i + 1
            if crit_level == 5:
                label = f'Criticality {crit_level} (highest)'
            elif crit_level == 1:
                label = f'Criticality {crit_level} (lowest)'
            else:
                label = f'Criticality {crit_level}'
            
            patch = mpatches.Patch(color=color, label=label)
            legend_patches.append(patch)
        
        if late_start:
            slack_patch = mpatches.Patch(color='gray', alpha=0.3, label='Slack time buffer')
            legend_patches.append(slack_patch)
        
        ax.legend(handles=legend_patches, loc='upper left', fontsize=10)
        
        # Styling
        ax.set_facecolor('#f8f9fa')
        
        plt.tight_layout()
        plt.savefig('gantt_chart.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        return fig, ax
        
    except Exception as e:
        # Silent fail - validation will catch issues
        return None, None

def plot_monte_carlo_histogram(project_durations: List[float], 
                              deadline: int = 30) -> Tuple[Optional[plt.Figure], Optional[plt.Axes]]:
    """
    Generate histogram of Monte Carlo simulation results
    Returns: (figure, axes) tuple or (None, None) on error
    """
    if len(project_durations) == 0: 
        return None, None
    
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.hist(
            project_durations, 
            bins=20,
            color='skyblue', 
            alpha=0.7,
            edgecolor='black'
        )
        
        # Deadline indicator
        ax.axvline(x=deadline, color='red', linestyle='--', linewidth=2, 
                   label=f'Deadline: {deadline} days')
        
        # Calculate statistics
        mean_duration = np.mean(project_durations)
        median_duration = np.median(project_durations)
        
        # Statistics text box
        stats_text = f"""Statistics:
Simulations: {len(project_durations)}
Mean: {mean_duration:.1f} days
Median: {median_duration:.1f} days
Min: {np.min(project_durations):.1f} days  
Max: {np.max(project_durations):.1f} days"""
        
        ax.text(
            0.98, 0.98,
            stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            fontsize=8
        )
        
        # Labels and styling
        ax.set_title('Project Duration Distribution (Monte Carlo)')
        ax.set_xlabel('Duration (days)')
        ax.set_ylabel('Frequency')
        ax.legend()  
        ax.grid(True, alpha=0.3)
        
        plt.savefig('monte_carlo_histogram.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        return fig, ax
        
    except Exception:
        return None, None

def plot_employee_load_heatmap(project, early_start: Dict, early_finish: Dict) -> Tuple:
    """
    Generate employee workload heatmap across project timeline
    Returns: (figure, axes, load_matrix) or (None, None, None) on error
    """
    try:
        # Determine project date range
        dates_list = list(early_start.values()) + list(early_finish.values())
        if not dates_list:
            return None, None, None
            
        project_start = min(dates_list)
        project_end = max(dates_list)
        project_days = (project_end - project_start).days + 1 
        
        # Create load matrix
        employees = list(project.proj_employees.values())
        if not employees:
            return None, None, None
            
        load_matrix = np.zeros((len(employees), project_days))
        
        # Populate load matrix
        for emp_idx, employee in enumerate(employees):
            for task_id in employee.emp_assigned_tasks:
                if task_id in early_start and task_id in early_finish:
                    task_start = early_start[task_id]
                    task_end = early_finish[task_id]
                    
                    start_day = (task_start - project_start).days
                    end_day = (task_end - project_start).days
                    
                    start_day = max(0, start_day)
                    end_day = min(project_days, end_day + 1)
                    
                    if start_day < end_day:
                        load = getattr(employee, 'emp_current_load', 1.0)
                        load_matrix[emp_idx, start_day:end_day] += load
        
        # Create heatmap visualization
        fig, ax = plt.subplots(figsize=(15, 6))
        
        im = ax.imshow(
            load_matrix,
            aspect='auto',
            cmap='RdYlBu_r',
            interpolation='nearest',
            vmin=0, vmax=12
        )
        
        # Configure axes
        ax.set_yticks(range(len(employees)))
        ax.set_yticklabels([emp.emp_name for emp in employees])
        
        date_labels = []
        tick_positions = []
        for i in range(0, project_days, 5):
            date = project_start + timedelta(days=i)
            date_labels.append(date.strftime('%d.%m'))
            tick_positions.append(i)
        
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(date_labels, rotation=45)
        
        # Color bar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Hours per day')
        
        # Grid lines between employees
        for i in range(1, len(employees)):
            ax.axhline(y=i-0.5, color='gray', linestyle='-', alpha=0.3, linewidth=0.5)
        
        # Highlight overloaded employees
        for emp_idx, employee in enumerate(employees):
            avg_load = np.mean(load_matrix[emp_idx, :])
            max_hours = getattr(employee, 'emp_max_daily_hours', 8)
            if avg_load > max_hours:
                ax.axhline(y=emp_idx, color='red', linewidth=2, alpha=0.5)
                ax.text(project_days * 0.02, emp_idx, f" Overload: {avg_load:.1f}h/day", 
                       va='center', color='red', fontweight='bold', fontsize=9,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
        
        # Final labels
        ax.set_xlabel('Project day')
        ax.set_ylabel('Employee')
        ax.set_title('Team Workload Distribution Heatmap')
        
        plt.tight_layout()
        plt.savefig('employee_load_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        return fig, ax, load_matrix
        
    except Exception:
        return None, None, None
    
def plot_skills_radar_chart(project) -> Optional[Dict]:
    """
    Generate skills gap analysis radar chart
    Returns: Analysis dictionary or None on error
    """
    try:
        # Collect unique skills
        all_skills = set()
        
        for employee in project.proj_employees.values():
            if employee.emp_skills:
                all_skills.update(employee.emp_skills)
        
        for task in project.proj_tasks.values():
            if task.task_skills:
                all_skills.update(task.task_skills)
        
        skills_list = sorted(list(all_skills))
        
        if not skills_list or len(skills_list) < 3:
            return None

        # Calculate team efficiency
        team_efficiency = {}
        
        for skill in skills_list:
            ratings = []
            
            for employee in project.proj_employees.values():
                if hasattr(employee, 'emp_efficiency') and employee.emp_efficiency:
                    if skill in employee.emp_efficiency:
                        ratings.append(employee.emp_efficiency[skill])
                elif hasattr(employee, 'emp_skills'):
                    if skill in employee.emp_skills:
                        ratings.append(1.0)
            
            if ratings:
                team_efficiency[skill] = np.mean(ratings)
            else:
                team_efficiency[skill] = 0
        
        # Calculate project needs
        project_needs = {}
        
        for skill in skills_list:
            total_need = 0
            
            for task in project.proj_tasks.values():
                if task.task_skills and skill in task.task_skills:
                    total_need += task.task_crit
            
            project_needs[skill] = total_need
        
        # Normalize data
        def normalize_data(data_dict: Dict) -> Dict:
            if not data_dict:
                return {}
            max_val = max(data_dict.values()) if max(data_dict.values()) > 0 else 1
            return {k: v / max_val for k, v in data_dict.items()}
        
        team_norm = normalize_data(team_efficiency)
        needs_norm = normalize_data(project_needs)
        
        # Prepare radar chart data
        categories = skills_list
        N = len(categories)
        
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]
        
        # Create radar chart
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        ax.set_theta_offset(pi / 2)
        ax.set_theta_direction(-1)
        
        team_values = [team_norm.get(skill, 0) for skill in categories]
        team_values += team_values[:1]
        
        needs_values = [needs_norm.get(skill, 0) for skill in categories]
        needs_values += needs_values[:1]
        
        # Plot data
        ax.plot(angles, team_values, 'o-', linewidth=2, color='blue',
                markersize=8, label='Team efficiency')
        
        ax.plot(angles, needs_values, 'o-', linewidth=2, color='red',
                markersize=8, label='Project requirements')
        
        # Fill areas
        ax.fill(angles, team_values, alpha=0.25, color='blue')
        ax.fill(angles, needs_values, alpha=0.25, color='red')
        
        # Configure axes
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        
        ax.set_ylim(0, 1.2)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=9)
        
        ax.grid(True, alpha=0.3)
        
        # Legend and title
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        # Calculate overall gap
        def calculate_gap(team: Dict, needs: Dict) -> float:
            if not team or not needs:
                return 0
            total_gap = sum(max(0, needs[k] - team[k]) for k in team)
            return total_gap / len(team)
        
        gap_percent = calculate_gap(team_norm, needs_norm)
        
        title = f'Team Skills vs Project Requirements\nAverage gap: {gap_percent:.1%}'
        ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
        
        # Highlight critical gaps
        skill_gaps = {}
        for skill in categories:
            gap = needs_norm.get(skill, 0) - team_norm.get(skill, 0)
            if gap > 0.3:
                skill_gaps[skill] = gap
        
        if skill_gaps:
            text = 'Critical skill gaps:\n'
            for skill, gap in sorted(skill_gaps.items(), key=lambda x: x[1], reverse=True)[:3]:
                text += f'• {skill}: {gap:.0%}\n'
            
            fig.text(1.5, 0.5, text, transform=ax.transAxes, fontsize=9,
                     bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.3))
        
        # Save chart
        plt.tight_layout()
        plt.savefig('skills_radar_chart.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return {
            'skills': skills_list,
            'team_efficiency': team_efficiency,
            'project_needs': project_needs,
            'team_norm': team_norm,
            'needs_norm': needs_norm,
            'skill_gaps': skill_gaps,
            'total_gap': gap_percent
        }
        
    except Exception:
        return None
