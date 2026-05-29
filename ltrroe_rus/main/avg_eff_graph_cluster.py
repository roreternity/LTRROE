"""
Группировка реальных проектов по прокси-эффективности команды.

Скрипт строит диагностические boxplot-графики для проверки того, как
avg_employee_efficiency связан с длительностью проекта, P50, Schedule Risk Ratio
и смещением P50 относительно детерминированной оценки.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
FILES_DIR = BASE_DIR / "files"
VIS_DIR = BASE_DIR / "visual" / "final"
VIS_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(FILES_DIR / 'metrics_results_full.csv')
df = df[df['mc_success'] == True].dropna(subset=['avg_employee_efficiency'])

# Группировка
df['eff_group'] = pd.cut(df['avg_employee_efficiency'],
                         bins=[0, 1.0, 2.0, float('inf')],
                         labels=['<1.0 (план занижен)', '1.0 (план = факт)', '>1.0 (план завышен)'])

# Статистика по группам
print("\n=== Сравнение групп по эффективности ===")
for group, sub in df.groupby('eff_group'):
    print(f"\n{group} (n={len(sub)}):")
    print(f"  det_duration days:  mean={sub['det_duration_days'].mean():.1f},  med={sub['det_duration_days'].median():.1f}")
    print(f"  p50 days:           mean={sub['p50'].mean():.1f},  med={sub['p50'].median():.1f}")
    print(f"  schedule_risk_ratio:mean={sub['schedule_risk_ratio'].mean():.3f}, med={sub['schedule_risk_ratio'].median():.3f}")
    print(f"  det_vs_p50_delta:   mean={sub['det_vs_p50_delta'].mean():.2f}, med={sub['det_vs_p50_delta'].median():.2f}")

# Графики
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
sns.boxplot(data=df, x='eff_group', y='det_duration_days', ax=axes[0,0])
axes[0,0].set_title('Детерминистическая длительность')
sns.boxplot(data=df, x='eff_group', y='p50', ax=axes[0,1])
axes[0,1].set_title('Медианная длительность (МК)')
sns.boxplot(data=df, x='eff_group', y='schedule_risk_ratio', ax=axes[1,0])
axes[1,0].set_title('Коэффициент риска (P90-P50)/P50')
sns.boxplot(data=df, x='eff_group', y='det_vs_p50_delta', ax=axes[1,1])
axes[1,1].set_title('Смещение детерм. оценки (P50 - det)')
plt.tight_layout()
plt.savefig(VIS_DIR / 'efficiency_groups.png', dpi=150)
