"""
Модуль визуализации результатов анализа
Создание графиков и диаграмм на основе данных моделирования

Основные функции:
- plot_gantt_chart() - диаграмма Ганта проекта с цветовой кодировкой критичности
- plot_monte_carlo_histogram() - распределение результатов симуляции с доверительными интервалами
- plot_employee_load_heatmap() - тепловая карта загрузки сотрудников с выделением перегрузок
- plot_skills_radar_chart() - радар-диаграмма навыков команды с анализом разрывов
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
    Создать диаграмму Ганта, отображающую задачи как горизонтальные полосы
    Возвращает: (фигура, оси) или (None, None) при ошибке
    """
    try: 
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Сортируем задачи по дате начала
        sorted_tasks = sorted(early_start.items(), key=lambda x: x[1])
    
        # Цвета по критичности
        colors = ['#FF6B6B', '#FFA726', '#FFD166', '#06D6A0', '#118AB2']
        
        y_positions = []
        task_labels = []
        
        for i, (task_id, start_date) in enumerate(sorted_tasks):
            task = project.proj_tasks[task_id]
            
            # Преобразуем даты в числовой формат для matplotlib
            start_num = mdates.date2num(start_date)
            end_date = early_finish[task_id]
            end_num = mdates.date2num(end_date)
            duration_days = (end_date - start_date).days
            
            # Определяем цвет по критичности (1-5)
            color_index = min(task.task_crit - 1, 4) if 1 <= task.task_crit <= 5 else 0
            
            # Нарисовать полосу задачи
            ax.barh(
                y=i,
                width=duration_days,
                left=start_num,
                height=0.6,
                color=colors[color_index],
                edgecolor='black',
                linewidth=1
            )
            
            # Добавить текст с названием задачи внутри полосы
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
            task_labels.append(f"Задача {task_id}")
        
        # Настройка осей
        ax.set_yticks(y_positions)
        ax.set_yticklabels(task_labels)
        
        # Форматирование дат на оси X
        ax.xaxis_date() 
        date_fmt = mdates.DateFormatter('%d.%m')
        ax.xaxis.set_major_formatter(date_fmt)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=45)
        
        # Подписи и заголовок
        ax.set_xlabel('Дата')
        ax.set_title('Диаграмма Ганта проекта')
        ax.grid(True, alpha=0.3, linestyle='--', which='both')
        
        # Легенда
        legend_patches = []
        for i, color in enumerate(colors):
            crit_level = i + 1
            if crit_level == 5:
                label = f'Критичность {crit_level} (самая высокая)'
            elif crit_level == 1:
                label = f'Критичность {crit_level} (самая низкая)'
            else:
                label = f'Критичность {crit_level}'
            
            patch = mpatches.Patch(color=color, label=label)
            legend_patches.append(patch)
        
        if late_start:
            slack_patch = mpatches.Patch(color='gray', alpha=0.3, label='Резерв времени (slack)')
            legend_patches.append(slack_patch)
        
        ax.legend(handles=legend_patches, loc='upper left', fontsize=10)
        
        # Стиль
        ax.set_facecolor('#f8f9fa')
        
        plt.tight_layout()
        plt.savefig('gantt_chart.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        return fig, ax
        
    except Exception:
        return None, None

def plot_monte_carlo_histogram(project_durations: List[float], 
                              deadline: int = 30) -> Tuple[Optional[plt.Figure], Optional[plt.Axes]]:
    """
    Создать гистограмму результатов симуляции Монте-Карло
    Возвращает: (фигура, оси) или (None, None) при ошибке
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
        
        # Линия дедлайна
        ax.axvline(x=deadline, color='red', linestyle='--', linewidth=2, 
                   label=f'Дедлайн: {deadline} дней')
        
        # Рассчитываем статистику
        mean_duration = np.mean(project_durations)
        median_duration = np.median(project_durations)
        
        # Текст со статистикой
        stats_text = f"""Статистика:
Симуляций: {len(project_durations)}
Среднее: {mean_duration:.1f} дней
Медиана: {median_duration:.1f} дней
Мин: {np.min(project_durations):.1f} дней  
Макс: {np.max(project_durations):.1f} дней"""
        
        ax.text(
            0.98, 0.98,
            stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            fontsize=8
        )
        
        # Подписи и стиль
        ax.set_title('Распределение длительности проекта (Monte Carlo)')
        ax.set_xlabel('Длительность (дни)')
        ax.set_ylabel('Частота')
        ax.legend()  
        ax.grid(True, alpha=0.3)
        
        plt.savefig('monte_carlo_histogram.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        return fig, ax
        
    except Exception:
        return None, None

def plot_employee_load_heatmap(project, early_start: Dict, early_finish: Dict) -> Tuple:
    """
    Создать тепловую карту загрузки сотрудников по дням проекта
    Возвращает: (фигура, оси, матрица_нагрузки) или (None, None, None) при ошибке
    """
    try:
        # Определяем диапазон дат проекта
        dates_list = list(early_start.values()) + list(early_finish.values())
        if not dates_list:
            return None, None, None
            
        project_start = min(dates_list)
        project_end = max(dates_list)
        project_days = (project_end - project_start).days + 1 
        
        # Создаём матрицу нагрузки
        employees = list(project.proj_employees.values())
        if not employees:
            return None, None, None
            
        load_matrix = np.zeros((len(employees), project_days))
        
        # Заполняем матрицу данными
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
        
        # Создаём тепловую карту
        fig, ax = plt.subplots(figsize=(15, 6))
        
        im = ax.imshow(
            load_matrix,
            aspect='auto',
            cmap='RdYlBu_r',
            interpolation='nearest',
            vmin=0, vmax=12
        )
        
        # Настройка осей
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
        
        # Цветовая шкала
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Часов в день')
        
        # Линии разделения между сотрудниками
        for i in range(1, len(employees)):
            ax.axhline(y=i-0.5, color='gray', linestyle='-', alpha=0.3, linewidth=0.5)
        
        # Выделение перегруженных сотрудников
        for emp_idx, employee in enumerate(employees):
            avg_load = np.mean(load_matrix[emp_idx, :])
            max_hours = getattr(employee, 'emp_max_daily_hours', 8)
            if avg_load > max_hours:
                ax.axhline(y=emp_idx, color='red', linewidth=2, alpha=0.5)
                ax.text(project_days * 0.02, emp_idx, f" Перегрузка: {avg_load:.1f}ч/день", 
                       va='center', color='red', fontweight='bold', fontsize=9,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
        
        # Заголовки
        ax.set_xlabel('День проекта')
        ax.set_ylabel('Сотрудник')
        ax.set_title('Загрузка сотрудников по дням проекта')
        
        plt.tight_layout()
        plt.savefig('employee_load_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        return fig, ax, load_matrix
        
    except Exception:
        return None, None, None
    
def plot_skills_radar_chart(project) -> Optional[Dict]:
    """
    Создать радар-диаграмму анализа навыков команды
    Возвращает: Словарь с результатами анализа или None при ошибке
    """
    try:
        # Собираем уникальные навыки
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

        # Рассчитываем среднюю эффективность команды
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
        
        # Рассчитываем потребности проекта в навыках
        project_needs = {}
        
        for skill in skills_list:
            total_need = 0
            
            for task in project.proj_tasks.values():
                if task.task_skills and skill in task.task_skills:
                    total_need += task.task_crit
            
            project_needs[skill] = total_need
        
        # Нормализация данных (0-1)
        def normalize_data(data_dict: Dict) -> Dict:
            if not data_dict:
                return {}
            max_val = max(data_dict.values()) if max(data_dict.values()) > 0 else 1
            return {k: v / max_val for k, v in data_dict.items()}
        
        team_norm = normalize_data(team_efficiency)
        needs_norm = normalize_data(project_needs)
        
        # Подготовка данных для радар-диаграммы
        categories = skills_list
        N = len(categories)
        
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]
        
        # Создаём радар-диаграмму
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        ax.set_theta_offset(pi / 2)
        ax.set_theta_direction(-1)
        
        team_values = [team_norm.get(skill, 0) for skill in categories]
        team_values += team_values[:1]
        
        needs_values = [needs_norm.get(skill, 0) for skill in categories]
        needs_values += needs_values[:1]
        
        # Рисуем графики
        ax.plot(angles, team_values, 'o-', linewidth=2, color='blue',
                markersize=8, label='Эффективность команды')
        
        ax.plot(angles, needs_values, 'o-', linewidth=2, color='red',
                markersize=8, label='Потребности проекта')
        
        # Заливаем области
        ax.fill(angles, team_values, alpha=0.25, color='blue')
        ax.fill(angles, needs_values, alpha=0.25, color='red')
        
        # Настраиваем оси
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        
        ax.set_ylim(0, 1.2)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=9)
        
        ax.grid(True, alpha=0.3)
        
        # Легенда и заголовок
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        # Рассчитываем общий разрыв
        def calculate_gap(team: Dict, needs: Dict) -> float:
            if not team or not needs:
                return 0
            total_gap = sum(max(0, needs[k] - team[k]) for k in team)
            return total_gap / len(team)
        
        gap_percent = calculate_gap(team_norm, needs_norm)
        
        title = f'Навыки команды vs Потребности проекта\nСредний разрыв: {gap_percent:.1%}'
        ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
        
        # Выделяем критические разрывы
        skill_gaps = {}
        for skill in categories:
            gap = needs_norm.get(skill, 0) - team_norm.get(skill, 0)
            if gap > 0.3:
                skill_gaps[skill] = gap
        
        if skill_gaps:
            text = 'Критические разрывы:\n'
            for skill, gap in sorted(skill_gaps.items(), key=lambda x: x[1], reverse=True)[:3]:
                text += f'• {skill}: {gap:.0%}\n'
            
            fig.text(1.5, 0.5, text, transform=ax.transAxes, fontsize=9,
                     bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.3))
        
        # Сохраняем диаграмму
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
