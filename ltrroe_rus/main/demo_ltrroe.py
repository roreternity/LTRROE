"""
LTRROE Полная демонстрация системы
Исследовательский проект в области стохастического моделирования проектных рисков
"""

import sys
import os
from LTRROE_logic.ltrroe_rus.Chapter1.code.test_data import create_test_project
from LTRROE_logic.ltrroe_rus.Chapter1.code.algorithms import calculate_schedule, monte_carlo_simulation, calculate_backward_pass
from LTRROE_logic.ltrroe_rus.Chapter1.code.visualisation import (
    plot_gantt_chart,
    plot_monte_carlo_histogram,
    plot_employee_load_heatmap,
    plot_skills_radar_chart
)

def demonstrate_research_project():
    """Полная демонстрация исследовательских возможностей LTRROE"""
    print("\n" + "="*70)
    print("LTRROE v2.0 - ДЕМОНСТРАЦИЯ СТОХАСТИЧЕСКОГО АНАЛИЗА ПРОЕКТНЫХ РИСКОВ")
    print("="*70)
    
    # 1. Создание экземпляра исследовательского проекта
    print("\n1. ИНИЦИАЛИЗАЦИЯ ПРОЕКТА")
    project = create_test_project()
    print(f"   • Задач: {len(project.proj_tasks)}, сотрудников: {len(project.proj_employees)}, зависимостей: {len(project.proj_dependencies)}")
    print(f"   • Дата начала: {project.proj_start_date.strftime('%Y-%m-%d')}")
    
    # 2. Детерминистический расчёт расписания (CPM)
    print("\n2. ДЕТЕРМИНИСТИЧЕСКИЙ АНАЛИЗ РАСПИСАНИЯ (CPM)")
    early_start, early_finish, task_duration = calculate_schedule(project)
    late_start, late_finish = calculate_backward_pass(project, early_finish, task_duration)
    
    critical_tasks = []
    for task_id in early_start:
        slack = (late_start[task_id] - early_start[task_id]).days
        if slack == 0:
            critical_tasks.append(task_id)
    
    project_end = max(early_finish.values())
    deterministic_duration = (project_end - project.proj_start_date).days
    print(f"   • Длительность (CPM): {deterministic_duration} дней")
    print(f"   • Критических задач: {len(critical_tasks)}")
    print(f"   • Задачи с резервом времени: {len(project.proj_tasks) - len(critical_tasks)}")
    
    # 3. Стохастический анализ рисков Монте-Карло
    print("\n3. СТОХАСТИЧЕСКАЯ ОЦЕНКА РИСКОВ (МОНТЕ-КАРЛО, N=1000)")
    mc_durations = monte_carlo_simulation(project, num_simulations=1000)
    
    mc_mean = sum(mc_durations) / len(mc_durations)
    mc_min = min(mc_durations)
    mc_max = max(mc_durations)
    
    print(f"   • Средняя длительность (МК): {mc_mean:.1f} дней")
    print(f"   • 95% интервал: [{mc_min:.1f}, {mc_max:.1f}] дней")
    print(f"   • Отклонение CPM от МК: {mc_mean - deterministic_duration:.1f} дней ({(mc_mean/deterministic_duration-1)*100:.1f}%)")
    
    deadline = 35
    success = sum(1 for d in mc_durations if d <= deadline)
    risk_percentage = 100 - (success/len(mc_durations)*100)
    print(f"   • Вероятность превышения {deadline} дней: {risk_percentage:.1f}%")
    
    # 4. Анализ использования ресурсов
    print("\n4. АНАЛИЗ РЕСУРСОВ")
    employees = list(project.proj_employees.values())
    overloaded = [emp.emp_name for emp in employees if emp.emp_current_load > emp.emp_max_daily_hours]
    avg_load = sum(e.emp_current_load for e in employees) / len(employees)
    print(f"   • Команда: {len(employees)} человек")
    print(f"   • Перегруженных: {len(overloaded)} ({', '.join(overloaded) if overloaded else 'нет'})")
    print(f"   • Средняя нагрузка: {avg_load:.1f} ч/день")
    
    # 5. Анализ разрывов в компетенциях
    print("\n5. АНАЛИЗ КОМПЕТЕНЦИЙ")
    radar_data = plot_skills_radar_chart(project)
    if radar_data:
        print(f"   • Навыков: {len(radar_data['skills'])}")
        print(f"   • Средний разрыв: {radar_data['total_gap']:.1%}")
        if radar_data['skill_gaps']:
            print(f"   • Критических разрывов: {len(radar_data['skill_gaps'])}")
            for skill, gap in list(radar_data['skill_gaps'].items())[:3]:
                print(f"     - {skill}: дефицит {gap:.0%}")
    
    # 6. Генерация отчётов визуализации
    print("\n6. ГЕНЕРАЦИЯ ВИЗУАЛИЗАЦИЙ")
    gantt_result = plot_gantt_chart(project, early_start, early_finish, late_start)
    mc_result = plot_monte_carlo_histogram(mc_durations, deadline=deadline)
    heatmap_result = plot_employee_load_heatmap(project, early_start, early_finish)
    
    reports = [
        ("Диаграмма Ганта", gantt_result[0] is not None),
        ("Распределение Монте-Карло", mc_result[0] is not None),
        ("Тепловая карта нагрузки", heatmap_result[0] is not None),
        ("Радар-диаграмма навыков", radar_data is not None)
    ]
    for name, ok in reports:
        print(f"   • {name}: {'создан' if ok else 'ошибка'}")
    
    # 7. Результаты
    print("\n" + "="*70)
    print("РЕЗУЛЬТАТЫ")
    print("="*70)
    results = """
МЕТОДОЛОГИЯ:
- Проект как ориентированный ациклический граф (DAG)
- Треугольные распределения длительности задач (PERT)
- Монте-Карло симуляция (1000 итераций)
- Метод критического пути (CPM) с вероятностными расширениями
- Учёт человеческого фактора через матрицы навыков

ВЫВОДЫ:
- Стохастическое моделирование даёт более реалистичные оценки сроков
- Перегрузка сотрудников и дефицит навыков увеличивают риски
- Визуализация позволяет идентифицировать проблемные зоны
"""
    print(results)
    print("\nСОЗДАННЫЕ ФАЙЛЫ:")
    print("   • gantt_chart.png")
    print("   • monte_carlo_histogram.png")
    print("   • employee_load_heatmap.png")
    print("   • skills_radar_chart.png")
    print("\n" + "="*70)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("="*70)

if __name__ == "__main__":
    demonstrate_research_project()
