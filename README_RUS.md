# LTRROE v2.0 — Local Team Resource & Risk Optimization Engine

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Система стохастического моделирования для оценки проектных рисков и оптимизации ресурсов.**

## Быстрый старт
```bash
# Клонировать репозиторий
git clone https://github.com/roreternity/LTRROE.git
cd LTRROE

# Установить зависимости
pip install matplotlib numpy

# Запустить демонстрацию
python demo_ltrroe.py
```

## Возможности
- **Моделирование Монте-Карло** - Вероятностное планирование проектов
- **Метод критического пути** - Сетевой анализ с учётом ресурсов
- **Моделирование человеческого фактора** - Оценка производительности по навыкам
- **Комплексная визуализация** - Четыре типа аналитических отчётов

## Структура проекта
```
RUS/
├── models.py              # Модели данных (Project, Task, Employee)
├── algorithmes.py         # Основные алгоритмы (CPM, Monte Carlo)
├── visualisation.py       # Модуль визуализации (4 типа графиков)
├── test_data.py           # Генератор тестовых проектов
└── demo_ltrroe.py         # Полная демонстрация
```

## Примеры использования
```python
from test_data import create_test_project
from algorithmes import calculate_schedule, monte_carlo_simulation
from visualisation import plot_gantt_chart

# Создание проекта и расчёт расписания
project = create_test_project()
early_start, early_finish, _ = calculate_schedule(project)

# Анализ рисков
durations = monte_carlo_simulation(project, num_simulations=1000)
print(f"Средняя длительность: {sum(durations)/len(durations):.1f} дней")

# Генерация диаграммы Ганта
plot_gantt_chart(project, early_start, early_finish)
```

## Генерируемые отчёты
- `gantt_chart.png` - Визуализация расписания с критическим путём
- `monte_carlo_histogram.png` - Распределение вероятностей
- `employee_load_heatmap.png` - Использование ресурсов
- `skills_radar_chart.png` - Анализ компетенций

## Исследовательский проект
Для академического контекста и методологии исследования см. README_ACADEMIC.md.

## Лицензия
MIT License. Подробнее в LICENSE.

## Контакты
**Автор:** roreternity  

**Проект:** https://github.com/roreternity/LTRROE
