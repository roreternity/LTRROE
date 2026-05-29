"""
Ранговая корреляция Спирмена для синтетического task-level датасета.

Скрипт показывает, какие признаки сильнее всего монотонно связаны с
фактической длительностью задачи.
"""

import pandas as pd
from scipy.stats import spearmanr
from pathlib import Path

FILES_DIR = Path(__file__).resolve().parents[1] / "files"
df = pd.read_csv(FILES_DIR / 'synthetic_tasks.csv')

features = [
    'planned_optimistic', 'planned_likely', 'planned_pessimistic',
    'criticality', 'cost',
    'assigned_avg_efficiency', 'assigned_total_load',
    'num_predecessors', 'num_successors'
]

results = []
for f in features:
    corr, pval = spearmanr(df[f], df['actual_duration'])
    results.append({'Feature': f, 'ρ (Spearman)': round(corr, 3), 'p-value': round(pval, 4)})

print(pd.DataFrame(results).sort_values('ρ (Spearman)', key=abs, ascending=False))
