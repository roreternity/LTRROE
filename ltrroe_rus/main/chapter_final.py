"""
Генерация графиков для главы "Валидация на реальном датасете Gryzzly".
Запускать с актуальным metrics_results_full.csv (после последнего прогона).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from pathlib import Path

# ── Настройки стиля (академический) ──────────────────────────────────────────
plt.rcParams.update({
    'font.family':     'DejaVu Sans',
    'font.size':       11,
    'axes.titlesize':  12,
    'axes.titleweight':'bold',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi':      150,
    'savefig.dpi':     300,
    'savefig.bbox':    'tight',
})
BLUE   = '#2563EB'
ORANGE = '#EA580C'
GRAY   = '#6B7280'
OUT    = Path("figures_real")
OUT.mkdir(exist_ok=True)

# ── Загрузка и фильтрация ─────────────────────────────────────────────────────
df = pd.read_csv("LTRROE_3/ltrroe_rus/files/metrics_results_full.csv")
df = df[df['mc_success'] == True].copy()

# Убираем явные выбросы (det > 500 дней — единичные аномальные проекты)
df = df[df['det_duration_days'] <= 500]
df = df[df['p50'] <= 600]
df = df.dropna(subset=['schedule_risk_ratio', 'p50', 'p90',
                        'det_duration_days', 'avg_employee_efficiency'])

print(f"Проектов для анализа: {len(df)}")
print(df[['schedule_risk_ratio','det_duration_days','p50','p90',
          'avg_employee_efficiency','n_tasks']].describe().round(2))


# ═══════════════════════════════════════════════════════════════════════════════
# Рис. A — Распределение schedule risk ratio
# Главный результат главы
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 4.5))

sns.histplot(df['schedule_risk_ratio'], bins=40, color=BLUE,
             edgecolor='white', linewidth=0.5, ax=ax)

med = df['schedule_risk_ratio'].median()
mean_ = df['schedule_risk_ratio'].mean()
ax.axvline(med,  color=ORANGE, lw=2, linestyle='--', label=f'Медиана = {med:.2f}')
ax.axvline(mean_, color=GRAY,  lw=1.5, linestyle=':',  label=f'Среднее  = {mean_:.2f}')
ax.set_xlim(left=0, right=0.5)

ax.set_xlabel('Schedule Risk Ratio  (P90 − P50) / P50', labelpad=8)
ax.set_ylabel('Количество проектов')
ax.set_title('Распределение стохастического риска расписания\n(реальные проекты Gryzzly, N = {:,})'.format(len(df)))
ax.legend()
fig.savefig(OUT / 'A_risk_distribution.png')
plt.close()
print("✓ A_risk_distribution.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Рис. B — Детерминированная оценка vs P50 (Monte Carlo)
# Показывает смещение CPM
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 6))

ax.scatter(df['det_duration_days'], df['p50'],
           alpha=0.35, s=20, color=BLUE, edgecolors='none')
lim = max(df['det_duration_days'].max(), df['p50'].max()) * 1.05
ax.plot([0, lim], [0, lim], '--', color=GRAY, lw=1.5, label='Det = P50 (идеал)')

# Линия регрессии
z = np.polyfit(df['det_duration_days'], df['p50'], 1)
p = np.poly1d(z)
xs = np.linspace(0, lim, 200)
ax.plot(xs, p(xs), color=ORANGE, lw=2, label=f'Регрессия (slope={z[0]:.2f})')

ax.set_xlabel('Детерминированная длительность (CPM), дней')
ax.set_ylabel('P50 Монте-Карло, дней')
ax.set_title('CPM vs Монте-Карло P50\n median delta = 0 days')
ax.set_xlim(0, lim); ax.set_ylim(0, lim)
ax.legend()
fig.savefig(OUT / 'B_det_vs_p50.png')
plt.close()
print("✓ B_det_vs_p50.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Рис. C — P50 vs P90 (неопределённость)
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 6))

ax.scatter(df['p50'], df['p90'],
           alpha=0.35, s=20, color=BLUE, edgecolors='none')
lim = max(df['p50'].max(), df['p90'].max()) * 1.05
ax.plot([0, lim], [0, lim], '--', color=GRAY, lw=1.5, label='P50 = P90')
ax.plot([0, lim], [0, lim * 1.2], color=ORANGE, lw=1.5,
        linestyle=':', label='+20% буфер')

ax.set_xlabel('P50 Монте-Карло, дней')
ax.set_ylabel('P90 Монте-Карло, дней')
ax.set_title('Разброс неопределённости: P50 → P90\nmedian P90/P50 = 1.17x')
ax.set_xlim(0, lim); ax.set_ylim(0, lim)
ax.legend()
fig.savefig(OUT / 'C_p50_vs_p90.png')
plt.close()
print("✓ C_p50_vs_p90.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Рис. D — Риск vs размер проекта (n_tasks)
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 4.5))

# Binned median
bins = [2, 4, 7, 11, 16, 25, 160]
labels = ['2–3', '4–6', '7–10', '11–15', '16–24', '25+']
df['task_bin'] = pd.cut(df['n_tasks'], bins=bins, labels=labels)
binned = df.groupby('task_bin', observed=True)['schedule_risk_ratio'].agg(
    ['median', 'mean', 'count']).reset_index()
binned.columns = ['bin', 'median', 'mean', 'count']

ax.bar(binned['bin'], binned['median'], color=BLUE,
       edgecolor='white', linewidth=0.5, label='Медиана риска')
for i, row in binned.iterrows():
    ax.text(i, row['median'] + 0.003, f'n={int(row["count"])}',
            ha='center', va='bottom', fontsize=9, color=GRAY)

ax.axhline(df['schedule_risk_ratio'].median(), color=ORANGE,
           lw=1.5, linestyle='--', label='Общая медиана')
ax.set_xlabel('Количество задач в проекте')
ax.set_ylabel('Schedule Risk Ratio (медиана)')
ax.set_title('Зависимость риска от размера проекта')
ax.legend()
fig.savefig(OUT / 'D_risk_vs_size.png')
plt.close()
print("✓ D_risk_vs_size.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Рис. E — Сводная таблица ключевых метрик (для вставки в статью)
# ═══════════════════════════════════════════════════════════════════════════════
summary = {
    'Метрика': [
        'Проектов (после фильтрации)',
        'Задач на проект (медиана)',
        'Сотрудников на проект (медиана)',
        'Детерминированная длительность, дней (медиана)',
        'P50 Монте-Карло, дней (медиана)',
        'P90 Монте-Карло, дней (медиана)',
        'Schedule Risk Ratio (медиана)',
        'Schedule Risk Ratio (среднее)',
        'Det vs P50 delta, дней (медиана)',
        'Avg Employee Efficiency (медиана)',
    ],
    'Значение': [
        f"{len(df):,}",
        f"{df['n_tasks'].median():.0f}",
        f"{df['n_employees'].median():.0f}",
        f"{df['det_duration_days'].median():.0f}",
        f"{df['p50'].median():.0f}",
        f"{df['p90'].median():.0f}",
        f"{df['schedule_risk_ratio'].median():.3f}",
        f"{df['schedule_risk_ratio'].mean():.3f}",
        f"{df['det_vs_p50_delta'].median():.1f}",
        f"{df['avg_employee_efficiency'].median():.2f}",
    ]
}
summary_df = pd.DataFrame(summary)

fig, ax = plt.subplots(figsize=(8, 4))
ax.axis('off')
tbl = ax.table(
    cellText=summary_df.values,
    colLabels=summary_df.columns,
    cellLoc='left', loc='center',
    colWidths=[0.72, 0.28]
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(10)
for (r, c), cell in tbl.get_celld().items():
    if r == 0:
        cell.set_facecolor('#1E3A5F')
        cell.set_text_props(color='white', fontweight='bold')
    elif r % 2 == 0:
        cell.set_facecolor('#F0F4FF')
    cell.set_edgecolor('#DDDDDD')
    cell.set_height(0.085)

ax.set_title('Сводные метрики: реальный датасет Gryzzly', pad=12,
             fontsize=12, fontweight='bold')
fig.savefig(OUT / 'E_summary_table.png')
plt.close()
print("✓ E_summary_table.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Рис. F — Корреляционная матрица
# ═══════════════════════════════════════════════════════════════════════════════
corr_cols = ['n_tasks', 'n_employees', 'n_dependencies',
             'critical_path_tasks', 'avg_employee_efficiency',
             'det_duration_days', 'schedule_risk_ratio']
corr = df[corr_cols].corr(method='spearman')
labels_ru = ['Задачи', 'Сотрудники', 'Зависимости',
             'Крит. путь', 'Эффективность', 'Det длит.', 'Risk Ratio']

fig, ax = plt.subplots(figsize=(7, 6))
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
            center=0, vmin=-1, vmax=1, linewidths=0.5,
            xticklabels=labels_ru, yticklabels=labels_ru,
            annot_kws={'size': 9}, ax=ax)
ax.set_title('Ранговая корреляция Спирмена\n(реальный датасет)', pad=10)
plt.xticks(rotation=35, ha='right')
fig.savefig(OUT / 'F_spearman_correlation.png')
plt.close()
print("✓ F_spearman_correlation.png")


print(f"\nВсе графики сохранены в папку: {OUT.resolve()}")
print("\n=== КЛЮЧЕВЫЕ ЧИСЛА ДЛЯ ТЕКСТА СТАТЬИ ===")
print(f"N проектов:              {len(df)}")
print(f"Медиана risk ratio:      {df['schedule_risk_ratio'].median():.3f}  (~{df['schedule_risk_ratio'].median()*100:.0f}%)")
print(f"Среднее risk ratio:      {df['schedule_risk_ratio'].mean():.3f}")
print(f"P90/P50 ratio (медиана): {(df['p90']/df['p50']).median():.2f}x")
print(f"Det vs P50 delta медиана:{df['det_vs_p50_delta'].median():.1f} дней")
print(f"Эффективность медиана:   {df['avg_employee_efficiency'].median():.2f}")
corr_risk_tasks = df[['n_tasks','schedule_risk_ratio']].corr(method='spearman').iloc[0,1]
corr_risk_eff   = df[['avg_employee_efficiency','schedule_risk_ratio']].corr(method='spearman').iloc[0,1]
print(f"ρ(n_tasks, risk):        {corr_risk_tasks:.3f}")
print(f"ρ(efficiency, risk):     {corr_risk_eff:.3f}")