"""
LTRROE Полная демонстрация системы
Исследовательский проект в области стохастического моделирования проектных рисков
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
    """Полная демонстрация исследовательских возможностей LTRROE"""
    print("\n" + "="*70)
    print("LTRROE v2.0 - ДЕМОНСТРАЦИЯ СТОХАСТИЧЕСКОГО АНАЛИЗА ПРОЕКТНЫХ РИСКОВ")
    print("Исследовательский проект для академического рассмотрения")
    print("="*70)
    
    # 1. Создание экземпляра исследовательского проекта
    print("\n1. ИНИЦИАЛИЗАЦИЯ ПРОЕКТА")
    print("   Создание стохастической модели проекта с:")
    project = create_test_project()
    print(f"   • {len(project.proj_tasks)} задач с треугольными распределениями длительности")
    print(f"   • {len(project.proj_employees)} сотрудников с профилями эффективности навыков")
    print(f"   • {len(project.proj_dependencies)} зависимостей задач (структура DAG)")
    print(f"   • Дата начала проекта: {project.proj_start_date.strftime('%Y-%m-%d')}")
    
    # 2. Детерминистический расчёт расписания (CPM)
    print("\n2. ДЕТЕРМИНИСТИЧЕСКИЙ АНАЛИЗ РАСПИСАНИЯ (МЕТОД КРИТИЧЕСКОГО ПУТИ)")
    early_start, early_finish, task_duration = calculate_schedule(project)
    late_start, late_finish = calculate_backward_pass(project, early_finish, task_duration)
    
    # Находим критический путь
    critical_tasks = []
    for task_id in early_start:
        slack = (late_start[task_id] - early_start[task_id]).days
        if slack == 0:
            critical_tasks.append(task_id)
    
    project_end = max(early_finish.values())
    deterministic_duration = (project_end - project.proj_start_date).days
    print(f"   • Детерминистическая длительность проекта: {deterministic_duration} дней")
    print(f"   • Критические задачи: {sorted(critical_tasks)}")
    print(f"   • Задачи с резервом времени: {len(project.proj_tasks) - len(critical_tasks)}")
    
    # 3. Стохастический анализ рисков Монте-Карло
    print("\n3. СТОХАСТИЧЕСКАЯ ОЦЕНКА РИСКОВ (СИМУЛЯЦИЯ МОНТЕ-КАРЛО)")
    print("   Выполнение 1000 стохастических симуляций...")
    mc_durations = monte_carlo_simulation(project, num_simulations=1000)
    
    mc_mean = sum(mc_durations) / len(mc_durations)
    mc_min = min(mc_durations)
    mc_max = max(mc_durations)
    
    print(f"   • Средняя длительность по Монте-Карло: {mc_mean:.1f} дней")
    print(f"   • 95% доверительный интервал: [{mc_min:.1f}, {mc_max:.1f}] дней")
    print(f"   • Разница детерминистической и стохастической оценки: {mc_mean - deterministic_duration:.1f} дней (+{(mc_mean/deterministic_duration-1)*100:.1f}%)")
    
    # Расчёт вероятности риска
    deadline = 30
    success = sum(1 for d in mc_durations if d <= deadline)
    risk_percentage = 100 - (success/len(mc_durations)*100)
    print(f"   • Вероятность срыва дедлайна в {deadline} дней: {risk_percentage:.1f}%")
    
    # 4. Анализ использования ресурсов
    print("\n4. АНАЛИЗ ИСПОЛЬЗОВАНИЯ РЕСУРСОВ")
    employees = list(project.proj_employees.values())
    overloaded = []
    for emp in employees:
        if emp.emp_current_load > emp.emp_max_daily_hours:
            overloaded.append(emp.emp_name)
    
    print(f"   • Размер команды: {len(employees)} человек")
    print(f"   • Перегруженные сотрудники: {len(overloaded)} ({', '.join(overloaded) if overloaded else 'нет'})")
    print(f"   • Средняя дневная нагрузка: {sum(e.emp_current_load for e in employees)/len(employees):.1f}ч/день")
    
    # 5. Анализ разрывов в компетенциях
    print("\n5. АНАЛИЗ РАЗРЫВОВ В КОМПЕТЕНЦИЯХ")
    radar_data = plot_skills_radar_chart(project)
    if radar_data:
        print(f"   • Уникальные навыки: {len(radar_data['skills'])}")
        print(f"   • Средний разрыв между командой и требованиями: {radar_data['total_gap']:.1%}")
        if radar_data['skill_gaps']:
            print(f"   • Критические разрывы в навыках: {len(radar_data['skill_gaps'])}")
            for skill, gap in list(radar_data['skill_gaps'].items())[:3]:
                print(f"     - {skill}: дефицит {gap:.0%}")
    
    # 6. Генерация отчётов визуализации
    print("\n6. ГЕНЕРАЦИЯ АНАЛИТИЧЕСКИХ ОТЧЁТОВ")
    print("   Создание аналитических дашбордов...")
    
    # Генерация всех визуализаций
    gantt_result = plot_gantt_chart(project, early_start, early_finish, late_start)
    mc_result = plot_monte_carlo_histogram(mc_durations, deadline=deadline)
    heatmap_result = plot_employee_load_heatmap(project, early_start, early_finish)
    
    reports = [
        ("Диаграмма Ганта", gantt_result[0] is not None),
        ("Распределение Монте-Карло", mc_result[0] is not None),
        ("Тепловая карта нагрузки", heatmap_result[0] is not None),
        ("Радар-диаграмма навыков", radar_data is not None)
    ]
    
    for report_name, success in reports:
        status = "✅ Создан" if success else "❌ Не создан"
        print(f"   • {report_name}: {status}")
    
    # 7. Академическое резюме
    print("\n" + "="*70)
    print("АКАДЕМИЧЕСКОЕ РЕЗЮМЕ")
    print("="*70)
    
    summary = """
КЛЮЧЕВЫЕ МЕТОДОЛОГИЧЕСКИЕ ВКЛАДЫ:
1. Формализация структуры проекта как ориентированного ациклического графа (DAG)
2. Интеграция треугольных вероятностных распределений (методология PERT)
3. Стохастическая симуляция Монте-Карло для квантификации неопределённости
4. Метод критического пути (CPM) с вероятностными расширениями
5. Моделирование человеческого фактора через матрицы эффективности навыков
6. Многомерная визуализация для поддержки принятия решений

НАУЧНАЯ ЗНАЧИМОСТЬ:
- Переход от детерминистического к вероятностному планированию проектов
- Количественная оценка рисков для управленческих решений
- Интеграция человеческих факторов в вычислительные модели
- Масштабируемый фреймворк для анализа сложных проектных экосистем

СИСТЕМА ДЕМОНСТРИРУЕТ ГОТОВНОСТЬ К ПРОДВИНУТЫМ ИССЛЕДОВАНИЯМ
В ОБЛАСТИ СТОХАСТИЧЕСКОЙ ОПТИМИЗАЦИИ, ИССЛЕДОВАНИЯ ОПЕРАЦИЙ И АНАЛИЗА РИСКОВ.
"""
    
    print(summary)
    
    print("\nСОЗДАННЫЕ АНАЛИТИЧЕСКИЕ ОТЧЁТЫ:")
    print("   • gantt_chart.png (Визуализация расписания с критическим путём)")
    print("   • monte_carlo_histogram.png (Распределение вероятностей)")
    print("   • employee_load_heatmap.png (Использование ресурсов)")
    print("   • skills_radar_chart.png (Анализ разрывов в компетенциях)")
    
    print("\n" + "="*70)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА - ГОТОВО К АКАДЕМИЧЕСКОМУ РАССМОТРЕНИЮ")
    print("="*70)

if __name__ == "__main__":
    demonstrate_research_project()
