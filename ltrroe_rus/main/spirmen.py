import pandas as pd
from scipy.stats import spearmanr

df = pd.read_csv('synthetic_tasks27.csv')

features = [
    'planned_optimistic', 'planned_likely', 'planned_pessimistic',
    'criticality', 'cost',
    'assigned_avg_efficiency', 'assigned_total_load',
    'num_predecessors', 'num_successors'
]

results = []
for f in features:
    corr, pval = spearmanr(df[f], df['actual_duration'])
    results.append({'Feature': f, 'ρ (Spirmen)': round(corr, 3), 'p-value': round(pval, 4)})

print(pd.DataFrame(results).sort_values('ρ (Spirmen)', key=abs, ascending=False))