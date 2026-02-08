"""
Модуль визуализации результатов анализа проекта LTRROE
Создание графиков и диаграмм на основе данных моделирования

Основные функции:
- plot_gantt_chart() - диаграмма Ганта проекта с цветовой кодировкой критичности
- plot_monte_carlo_histogram() - распределение результатов симуляции с доверительными интервалами
- plot_employee_load_heatmap() - тепловая карта загрузки сотрудников с выделением перегрузок
- plot_skills_radar_chart() - радар-диаграмма навыков команды с анализом разрывов

Используется в рамках исследовательского прототипа LTRROE v2.0
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from math import pi

def plot_gantt_chart(project, early_start, early_finish, late_start=None):
    """
    Диаграмма Ганта - показывает задачи как горизонтальные полосы
    """
    try: 
        # Создаем холст
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Подготовка данных
        # Сортируем задачи по дате начала
        sorted_tasks = sorted(early_start.items(), key=lambda x: x[1])
    
        # Цвета по критичности
        colors = ['#FF6B6B', '#FFA726', '#FFD166', '#06D6A0', '#118AB2']
        
        # Рисуем каждую задачу
        y_positions = []
        task_labels = []
        
        for i, (task_id, start_date) in enumerate(sorted_tasks):
            task = project.proj_tasks[task_id]
            
            # Преобразуем даты в числа для matplotlib
            start_num = mdates.date2num(start_date)
            end_date = early_finish[task_id]
            end_num = mdates.date2num(end_date)
            duration_days = (end_date - start_date).days
            
            # Определяем цвет по критичности (1-5)
            color_index = min(task.task_crit - 1, 4) if 1 <= task.task_crit <= 5 else 0
            
            # Нарисовать полосу (используем числовые значения дат)
            ax.barh(
                y=i,
                width=duration_days,  # Используем дни как ширину
                left=start_num,  # Числовое значение даты
                height=0.6,
                color=colors[color_index],
                edgecolor='black',
                linewidth=1
            )
            
            # Добавить текст с названием задачи в середине полосы
            mid_point = start_num + duration_days / 2
            short_name = task.task_name[:15] + "..." if len(task.task_name) > 15 else task.task_name
            
            # Текст внутри полосы (белый)
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
        
        # Настройки осей
        ax.set_yticks(y_positions)
        ax.set_yticklabels(task_labels)
        
        # Форматируем даты на оси X
        ax.xaxis_date() 
        
        # Форматтер дат (день.месяц)
        date_fmt = mdates.DateFormatter('%d.%m')
        ax.xaxis.set_major_formatter(date_fmt)
        
        # Автоматически выбираем хорошие деления
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Поворачиваем подписи дат
        fig.autofmt_xdate(rotation=45)
        
        # Добавялем заголовок и подписи
        ax.set_xlabel('Дата')
        ax.set_title('Диаграмма Ганта проекта')
        ax.grid(True, alpha=0.3, linestyle='--', which='both')
        
        # Легенда с объяснением цветов
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
        
        # Добавляем информацию о slack если есть
        if late_start:
            slack_patch = mpatches.Patch(color='gray', alpha=0.3, label='Slack (запас времени)')
            legend_patches.append(slack_patch)
        
        ax.legend(handles=legend_patches, loc='upper left', fontsize=10)
        
        # Настройка внешки
        ax.set_facecolor('#f8f9fa')  # светло-серый
        
        # Сохранить и показать
        plt.tight_layout()
        
        # Сохраняем в файл
        plt.savefig('gantt_chart.png', dpi=300, bbox_inches='tight')
        plt.close(fig)  # закрываем график чтобы продолжить выполнение
        
        return fig, ax
        
    except Exception as e:
        print(f"❌ ОШИБКА в plot_gantt_chart: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def plot_monte_carlo_histogram(project_durations, deadline=30):
    if len(project_durations) == 0: 
        print("❌ Ошибка! Нет данных для гистограммы")
        return None
    
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.hist(
            project_durations, 
            bins=20,  # сколько столбцов
            color='skyblue', 
            alpha=0.7,
            edgecolor='black'  # границы столбцов
        )
        
        # Линия дедлайна 
        ax.axvline(x=deadline, color='red', linestyle='--', linewidth=2, 
                   label=f'Дедлайн: {deadline} дней')
        
        # Рассчитываем статистику
        mid_duration = sum(project_durations) / len(project_durations)
        
        # Медиана
        sorted_durations = sorted(project_durations)  
        n = len(sorted_durations)
        
        if n % 2 == 0:
            # Четное количество
            median_duration = (sorted_durations[n//2 - 1] + sorted_durations[n//2]) / 2
        else:
            # Нечетное количество
            median_duration = sorted_durations[n//2]
        
        # Статистический текст
        stats_text =f"""Статистика:
Симуляций: {len(project_durations)}
Среднее: {mid_duration:.1f} дней
Медиана: {median_duration:.1f} дней
Мин: {min(project_durations):.1f} дней  
Макс: {max(project_durations):.1f} дней"""
        
        # Добавляем текст в график
        ax.text(
            0.98, 0.98,  # Право, верх
            stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            horizontalalignment='right',  # Выравнивание по правому краю
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            fontsize=8
        )
        
        # Настройки
        ax.set_title('Распределение длительности проекта (Monte Carlo)')
        ax.set_xlabel('Длительность (дни)')
        ax.set_ylabel('Частота')
        # Легенда за пределами графика справа
        # Настройки
        ax.set_title('Распределение длительности проекта (Monte Carlo)')
        ax.set_xlabel('Длительность (дни)')
        ax.set_ylabel('Частота')
        ax.legend()  
        ax.grid(True, alpha=0.3)
        plt.savefig('monte_carlo_histogram.png', dpi=300, bbox_inches='tight')
        plt.close(fig)  # Закрываем график
        
        return fig, ax
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None

def plot_employee_load_heatmap(project, early_start, early_finish):
    """
    Heatmap загрузки сотрудников по дням
    """
    try:
        # Диапазон дат проекта
        dates_list = list(early_start.values()) + list(early_finish.values())
        if not dates_list:
            print("❌ Нет данных о датах задач")
            return None, None, None
            
        project_start = min(dates_list)
        project_end = max(dates_list)
        project_days = (project_end - project_start).days + 1 
        
        # Создание матрицы загрузки
        employees = list(project.proj_employees.values())
        if not employees:
            print("❌ Нет сотрудников в проекте!")
            return None, None, None
            
        load_matrix = np.zeros((len(employees), project_days))
        
        # Заполняем матрицу данными
        for emp_idx, employee in enumerate(employees):
            for task_id in employee.emp_assigned_tasks:
                if task_id in early_start and task_id in early_finish:
                    task_start = early_start[task_id]
                    task_end = early_finish[task_id]
                    
                    # Переводим даты в индексы дней
                    start_day = (task_start - project_start).days
                    end_day = (task_end - project_start).days
                    
                    # Убеждаемся что индексы в пределах матрицы
                    start_day = max(0, start_day)
                    end_day = min(project_days, end_day + 1)  # +1 чтобы включить последний день
                    
                    # Добавляем загрузку сотрудника на период задачи
                    if start_day < end_day:  # проверяем что период подходит
                        # Используем emp_current_load если есть, иначе 1
                        load = getattr(employee, 'emp_current_load', 1.0)
                        load_matrix[emp_idx, start_day:end_day] += load
        
        # Визуализация Heatmap
        fig, ax = plt.subplots(figsize=(15, 6))
        
        # imshow - показывает матрицу как изображение с цветами
        im = ax.imshow(
            load_matrix,           # данные матрицы
            aspect='auto',         # автоматические пропорции
            cmap='RdYlBu_r',       # цветовая схема (красный-жёлтый-синий, обратная)
            interpolation='nearest', # не сглаживать пиксели
            vmin=0, vmax=12         # значения от 0 до 12 часов
        )
        
        # Настройка осей
        # Y ось - сотрудники
        ax.set_yticks(range(len(employees)))
        ax.set_yticklabels([emp.emp_name for emp in employees])
        
        # X ось - даты (каждые 5 дней)
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
        
        # Линии разделения между сотрудникам
        for i in range(1, len(employees)):
            ax.axhline(y=i-0.5, color='gray', linestyle='-', alpha=0.3, linewidth=0.5)
        
        # Выделение перегруженных красной рамкой
        for emp_idx, employee in enumerate(employees):
            avg_load = np.mean(load_matrix[emp_idx, :])
            max_hours = getattr(employee, 'emp_max_daily_hours', 8)
            if avg_load > max_hours:
                ax.axhline(y=emp_idx, color='red', linewidth=2, alpha=0.5)
                # Добавляем текст о перегрузке
                ax.text(project_days * 0.02, emp_idx, f" Перегрузка: {avg_load:.1f}ч/день", 
                       va='center', color='red', fontweight='bold', fontsize=9,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
        
        # Заголовки и сохранение
        ax.set_xlabel('День проекта')
        ax.set_ylabel('Сотрудник')
        ax.set_title('Загрузка сотрудников по дням проекта (Heatmap)')
        
        plt.tight_layout()
        plt.savefig('employee_load_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        # Выводим статистику по загрузке
        print("\nСтатистика загрузки сотрудников:")
        print("=" * 40)
        for emp_idx, employee in enumerate(employees):
            avg_load = np.mean(load_matrix[emp_idx, :])
            max_load = np.max(load_matrix[emp_idx, :])
            max_hours = getattr(employee, 'emp_max_daily_hours', 8)
            
            status = "✅ OK" if avg_load <= max_hours else "⚠️ ПЕРЕГРУЗКА"
            print(f"{employee.emp_name}: средняя {avg_load:.1f}ч/день, пиковая {max_load:.1f}ч/день - {status}")
        
        return fig, ax, load_matrix
        
    except Exception as e:
        print(f"❌ Ошибка в plot_employee_load_heatmap: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None
    
def plot_skills_radar_chart(project):
    """
    Радар-диаграмма навыков команды
    """
    # Собрать уникальные навыки
    all_skills = set()
    
    # Собираем навыки сотрудников
    for employee in project.proj_employees.values():
        if employee.emp_skills:
            if isinstance(employee.emp_skills, dict):
                all_skills.update(employee.emp_skills.keys())
            else:
                all_skills.update(employee.emp_skills)
    
    # Собираем навыки из задач
    for task in project.proj_tasks.values():
        if task.task_skills:
            all_skills.update(task.task_skills)
    
    skills_list = sorted(list(all_skills))
    
    if not skills_list:
        print("❌ Нет данных о навыках")
        return None

    # Рассчитываем среднюю эффективность команды
    team_efficiency = {}
    
    for skill in skills_list:
        ratings = []
        
        for employee in project.proj_employees.values():
            # Проверяем эффективность сотрудника по этому навыку
            if hasattr(employee, 'emp_efficiency') and employee.emp_efficiency:
                if skill in employee.emp_efficiency:
                    ratings.append(employee.emp_efficiency[skill])
            # Или проверяем просто наличие навыка
            elif hasattr(employee, 'emp_skills'):
                if isinstance(employee.emp_skills, dict) and skill in employee.emp_skills:
                    ratings.append(employee.emp_skills[skill])
                elif skill in employee.emp_skills:
                    ratings.append(1.0)  # базовый уровень если навык есть
        
        if ratings:
            team_efficiency[skill] = sum(ratings) / len(ratings)
        else:
            team_efficiency[skill] = 0
    
    # Рассчитывем потребность проекта в навыках
    project_needs = {}
    
    for skill in skills_list:
        total_need = 0
        
        for task in project.proj_tasks.values():
            if task.task_skills and skill in task.task_skills:
                # Вес = критичность задачи
                weight = task.task_crit
                total_need += weight
        
        project_needs[skill] = total_need
    
    # Нормализация данных (0-1)
    def normalize_data(data_dict):
        if not data_dict:
            return {}
        
        max_val = max(data_dict.values()) if max(data_dict.values()) > 0 else 1
        return {k: v / max_val for k, v in data_dict.items()}
    
    team_norm = normalize_data(team_efficiency)
    needs_norm = normalize_data(project_needs)
    
    # Подготовить данные для радар-диаграммы
    categories = skills_list
    N = len(categories)
    
    if N < 3:
        print("❌ Слишком мало навыков для радар-диаграммы (нужно минимум 3)")
        return None
    
    # Углы для каждого навыка
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]  # замкнуть круг
    
    # Создать радар-диаграмму
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    # Настроить основные оси
    ax.set_theta_offset(pi / 2)  # повернуть на 90 градусов
    ax.set_theta_direction(-1)   # по часовой 
    
    # Добавить значения
    team_values = [team_norm.get(skill, 0) for skill in categories]
    team_values += team_values[:1]
    
    needs_values = [needs_norm.get(skill, 0) for skill in categories]
    needs_values += needs_values[:1]
    
    # Нарисовать графики
    ax.plot(angles, team_values, 'o-', linewidth=2, color='blue',
            markersize=8, label='Эффективность команды')
    
    ax.plot(angles, needs_values, 'o-', linewidth=2, color='red',
            markersize=8, label='Потребность проекта')
    
    # Залить области
    ax.fill(angles, team_values, alpha=0.25, color='blue')
    ax.fill(angles, needs_values, alpha=0.25, color='red')
    
    # Настроить оси
    ax.set_xticks(angles[:-1])  # не включать последний (дубликат)
    ax.set_xticklabels(categories, fontsize=10)
    
    ax.set_ylim(0, 1.2)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=9)
    
    # Сетка
    ax.grid(True, alpha=0.3)
    
    # Легенда и заголовок 
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    
    # Рассчитать общий разрыв
    def calculate_gap(team, needs):
        if not team or not needs:
            return 0
        total_gap = sum(max(0, needs[k] - team[k]) for k in team)
        return total_gap / len(team)
    
    gap_percent = calculate_gap(team_norm, needs_norm)
    
    title = 'Навыки команды vs Потребности проекта\n'
    title += f'Средний разрыв: {gap_percent:.1%}'
    ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
    
    # Добавить аналитику
    skill_gaps = {}
    for skill in categories:
        gap = needs_norm.get(skill, 0) - team_norm.get(skill, 0)
        if gap > 0.3:  # Разрыв больше 30%
            skill_gaps[skill] = gap
    
    if skill_gaps:
        text = 'Критические разрывы:\n'
        for skill, gap in sorted(skill_gaps.items(), key=lambda x: x[1], reverse=True)[:3]:
            text += f'• {skill}: {gap:.0%}\n'
        
        fig.text(1.5, 0.5, text, transform=ax.transAxes, fontsize=9,
                 bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.3))
    
    # Вывод статистики
    print("\nАнализ навыков:")
    print("=" * 40)
    for skill in skills_list:
        team_val = team_norm.get(skill, 0)
        need_val = needs_norm.get(skill, 0)
        gap_val = need_val - team_val
        
        if gap_val > 0.3:
            status = "🔴 КРИТИЧЕСКИЙ РАЗРЫВ"
        elif gap_val > 0:
            status = "🟡 Небольшой разрыв"
        elif gap_val == 0 and team_val > 0:
            status = "🟢 Полное соответствие"
        else:
            status = "⚪ Навык не требуется"
        
        print(f"{skill:15} | команда: {team_val:5.1%} | нужно: {need_val:5.1%} | {status}")
    
    # Сохранить
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

if __name__ == "__main__":
    """
    ТЕСТОВЫЙ РЕЖИМ: запускается при прямом запуске файла
    visualization.py
    """
    print("="*60)
    print("ЗАПУСК ТЕСТА ВИЗУАЛИЗАЦИИ")
    print("="*60)

    # Тестируем импорт данных
    print("\n1. Тестируем импорт данных...")
    try:
        from test_data import create_test_project
        project = create_test_project()
        print(f"\n   ✅ Проект создан: {len(project.proj_tasks)} задач")
        
        # Создаём тестовые данные для Ганта
        early_start = {}
        early_finish = {}
        
        # Простые даты для теста
        base_date = project.proj_start_date
        
        for task_id, task in project.proj_tasks.items():
            if task_id < 5:  # Только первые 5 задач
                start = base_date + timedelta(days=task_id * 5)
                duration = task.task_duration_dist[1]  # средняя длительность
                early_start[task_id] = start
                early_finish[task_id] = start + timedelta(days=duration)
        
        print(f"   ✅ Тестовые даты созданы для {len(early_start)} задач")
        
        # 3. ТЕСТИРУЕМ ДИАГРАММУ ГАНТТА
        print("\n2. Тестируем диаграмму Ганта...")
        fig, ax = plot_gantt_chart(project, early_start, early_finish)
        
        if fig:
            print("\n   ✅ Диаграмма Ганта создана!")
        else:
            print("   ❌ Не удалось создать диаграмму")
        
        # Тестируем гистограмму Монте-Карло
        print("\n3. Тестируем гистограмму Monte Carlo...")
        
        # Создаём тестовые данные (1000 симуляций)
        test_durations = []
        for _ in range(1000):
            # Случайное число от 25 до 45 дней
            test_durations.append(np.random.uniform(25, 45))
        
        print(f"\n   Создано {len(test_durations)} тестовых симуляций")
        
        fig_hist, ax_hist = plot_monte_carlo_histogram(test_durations, deadline=30)
        
        if fig_hist:
            print("   ✅ Гистограмма создана!")

        # Тест Heatmap загрузки
        print("\n4. Тестируем heatmap загрузки сотрудников...")
        result = plot_employee_load_heatmap(project, early_start, early_finish)

        if result and result[0] is not None:  # Проверяем что не None
            fig_heat, ax_heat, load_matrix = result
            print("\n   ✅ Heatmap создан!")
        else:
            print("   ⚠️ Heatmap не создан")
            fig_heat, ax_heat, load_matrix = None, None, None
        # Тест радар-диаграммы
        print("\n5. Тестируем радар-диаграмму навыков...")
        radar_result = plot_skills_radar_chart(project)
        
        if radar_result:
            print("\n   ✅ Радар-диаграмма создана!")
            
    except ImportError as e:
        print(f"   ❌ Не могу импортировать test_data: {e}")
        print("   Убедись что test_data.py в той же папке")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("ТЕСТ ЗАВЕРШЁН")
    print("="*60)
