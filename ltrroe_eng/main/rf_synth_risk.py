"""
Random Forest model for task-duration prediction.
Includes baseline comparison: PERT, PERT x mean slowdown, and PERT x analytical S_i.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_predict
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 1. Load data
BASE_DIR = Path(__file__).resolve().parents[1]
FILES_DIR = BASE_DIR / "files"
VIS_DIR = BASE_DIR / "visual" / "rf_synth_dur"
DATA_PATH = FILES_DIR / "synthetic_tasks.csv"
VIS_DIR.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(DATA_PATH)

print("Dataset size:", df.shape)
print("Mean task duration:", df['actual_duration'].mean().round(2), "days")
print("Median task duration:", df['actual_duration'].median().round(2), "days")

# 2. Features and target variable
features = [
    'planned_optimistic', 'planned_likely', 'planned_pessimistic',
    'criticality', 'cost',
    'assigned_avg_efficiency', 'assigned_total_load',
    'num_predecessors', 'num_successors'
]
X = df[features]
y = df['actual_duration']

# 3. Train/test split 
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Training sample: {len(X_train)} tasks")
print(f"Test sample: {len(X_test)} tasks")

# 4. Train Random Forest
model = RandomForestRegressor(
    n_estimators=300,
    max_depth=15,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)
print("Training Random Forest...")
model.fit(X_train, y_train)

# 5. Prediction and evaluation 
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\nRandom Forest results on the test split:")
print(f"  MAE : {mae:.2f} days")
print(f"  RMSE: {rmse:.2f} days")
print(f"  R²  : {r2:.3f}")

# 6. Feature importance 
importances = pd.Series(model.feature_importances_, index=features)
importances = importances.sort_values(ascending=False)
print("\nFeature importance:")
print(importances.round(4))

# 7. Save model
MODEL_PATH = FILES_DIR / 'ltrroe_randomforest_model.pkl'
joblib.dump(model, MODEL_PATH)
print(f"\nModel saved to: {MODEL_PATH}")

# 8. Save plots
# 8.1 Scatter plot: actual vs predicted
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Actual duration, days')
plt.ylabel('Predicted duration, days')
plt.title('Actual vs Predicted (Random Forest)')
plt.savefig(VIS_DIR / 'actual_vs_predicted_rf.png')
plt.close()

# 8.2 Error distribution
errors = y_test - y_pred
plt.figure(figsize=(10, 6))
sns.histplot(errors, bins=50, kde=True)
plt.xlabel('Error, days')
plt.title('Error distribution (Random Forest)')
plt.savefig(VIS_DIR / 'error_distribution_rf.png')
plt.close()

# 8.3 Feature-importance bar chart
plt.figure(figsize=(10, 6))
ax = importances.plot(kind='bar')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')  # rotate labels by 45 degrees
plt.title('Feature Importance (Random Forest)')
plt.ylabel('Contribution')
plt.tight_layout()
plt.savefig(VIS_DIR / 'feature_importance_rf.png')
plt.close()

# 9. Baselines on the full dataset
# Baseline B1: plain PERT
pert_pred = (df['planned_optimistic'] + 4 * df['planned_likely'] + df['planned_pessimistic']) / 6

# Baseline B2: PERT x mean slowdown
actual_slowdown = y / pert_pred
mean_slowdown = actual_slowdown.mean()
b2_pred = pert_pred * mean_slowdown

# Baseline B3: PERT x analytical slowdown from primary-assignee features
s_skill = np.where(
    df['primary_miss_ratio'] >= 1.0, 3.0,
    np.where(df['primary_miss_ratio'] > 0,
             2.0 + df['primary_miss_ratio'],
             1.0 / df['primary_min_efficiency'].clip(lower=0.1))
)
s_load = 1 + df['primary_overload'] * 0.05
b3_pred = pert_pred * s_skill * s_load

# ML on the full dataset via cross-validation, without leakage
ml_full_pred = cross_val_predict(
    RandomForestRegressor(n_estimators=300, max_depth=15, min_samples_split=5,
                          random_state=42, n_jobs=-1),
    X, y, cv=5
)

# ========================= 10. Model comparison =========================
def metrics(y_true, y_pred, label):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return {'Model': label, 'MAE': round(mae,2), 'RMSE': round(rmse,2), 'R²': round(r2,3)}

results = pd.DataFrame([
    metrics(y, pert_pred,       'B1: PERT (without human factor)'),
    metrics(y, b2_pred,         'B2: PERT × mean slowdown'),
    metrics(y, b3_pred,         'B3: PERT × analytical S_i'),
    metrics(y, ml_full_pred,    'ML: Random Forest (CV)'),
])

b1_mae = results.loc[results['Model'].str.startswith('B1'), 'MAE'].values[0]
results['MAE improvement vs B1'] = results['MAE'].apply(
    lambda x: f"{((b1_mae - x) / b1_mae * 100):.1f}%"
)

print("\n─── Baseline comparison ───")
print(results.to_string(index=False))

# MAE bar chart
fig, ax = plt.subplots(figsize=(9, 5))
colors = ['#c0392b', '#e67e22', '#f1c40f', '#27ae60']
ax.bar(results['Model'], results['MAE'], color=colors)
ax.set_ylabel('MAE, days')
ax.set_title('Baseline comparison: MAE by model level')
ax.set_xticklabels(results['Model'], rotation=15, ha='right')
for i, row in results.iterrows():
    ax.text(i, row['MAE'] + 0.3, f"{row['MAE']}", ha='center', fontsize=9)
plt.tight_layout()
plt.savefig(VIS_DIR / 'baseline_comparison_rf.png', dpi=150)
plt.close()
print(f"Saved: {VIS_DIR / 'baseline_comparison_rf.png'}")
