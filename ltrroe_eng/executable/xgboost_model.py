"""
XGBoost model for task duration prediction.
Includes baseline comparison (PERT, PERT×mean slowdown, PERT×analytic slowdown).
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_predict
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load data 
DATA_PATH = '/Users/roryqwork/Documents/Workspace/LTRROE/ltrroe_eng/datasets/synthetic_tasks.csv'
df = pd.read_csv(DATA_PATH)

print("Dataset shape:", df.shape)
print("Average task duration:", df['actual_duration'].mean().round(2), "days")
print("Median task duration:", df['actual_duration'].median().round(2), "days")

# 2. Features and target 
features = [
    'planned_optimistic', 'planned_likely', 'planned_pessimistic',
    'criticality', 'cost',
    'assigned_avg_efficiency', 'assigned_total_load',
    'num_predecessors', 'num_successors'
]
X = df[features]
y = df['actual_duration']

# 3. Train / test split 
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Training set: {len(X_train)} tasks")
print(f"Test set: {len(X_test)} tasks")

# 4. Train XGBoost 
model = XGBRegressor(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1,
    objective='reg:squarederror'
)
print("Training XGBoost...")
model.fit(X_train, y_train)

# 5. Predict & evaluate
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\nXGBoost results (test set):")
print(f"  MAE : {mae:.2f} days")
print(f"  RMSE: {rmse:.2f} days")
print(f"  R²  : {r2:.3f}")

# 6. Feature importance
importances = pd.Series(model.feature_importances_, index=features)
importances = importances.sort_values(ascending=False)
print("\nFeature importance:")
print(importances.round(4))

# 7. Save model 
MODEL_PATH = 'ltrroe_xgboost_model.pkl'
joblib.dump(model, MODEL_PATH)
print(f"\nModel saved to: {MODEL_PATH}")

# 8. Save plots 
# 8.1 Scatter: actual vs predicted
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Actual duration (days)')
plt.ylabel('Predicted duration (days)')
plt.title('Actual vs Predicted (XGBoost)')
plt.savefig('actual_vs_predicted_xgb.png')
plt.close()

# 8.2 Error distribution
errors = y_test - y_pred
plt.figure(figsize=(10, 6))
sns.histplot(errors, bins=50, kde=True)
plt.xlabel('Error (days)')
plt.title('Error distribution (XGBoost)')
plt.savefig('error_distribution_xgb.png')
plt.close()

# 8.3 Feature importance bar plot
plt.figure(figsize=(10, 6))
ax = importances.plot(kind='bar')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
plt.title('Feature importance (XGBoost)')
plt.ylabel('Contribution')
plt.tight_layout()
plt.savefig('feature_importance_xgb.png')
plt.close()

# 9. Baselines (full dataset)
# PERT baseline (B1)
pert_pred = (df['planned_optimistic'] + 4 * df['planned_likely'] + df['planned_pessimistic']) / 6

# B2: PERT × mean slowdown (average factor over whole dataset)
actual_slowdown = y / pert_pred
mean_slowdown = actual_slowdown.mean()
b2_pred = pert_pred * mean_slowdown

# B3: PERT × analytic slowdown from available features
s_skill = np.where(
    df['primary_miss_ratio'] >= 1.0, 3.0,
    np.where(df['primary_miss_ratio'] > 0,
             2.0 + df['primary_miss_ratio'],
             1.0 / df['primary_min_efficiency'].clip(lower=0.1))
)
s_load = 1 + df['primary_overload'] * 0.05
b3_pred = pert_pred * s_skill * s_load

# ML full predictions via 5‑fold cross‑validation (no data leakage)
ml_full_pred = cross_val_predict(
    XGBRegressor(
        n_estimators=500, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
        n_jobs=-1, objective='reg:squarederror'
    ),
    X, y, cv=5
)

# 10. Compare all models 
def metrics(y_true, y_pred, label):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return {'Model': label, 'MAE': round(mae,2), 'RMSE': round(rmse,2), 'R²': round(r2,3)}

results = pd.DataFrame([
    metrics(y, pert_pred,       'B1: PERT (no human factor)'),
    metrics(y, b2_pred,         'B2: PERT × mean slowdown'),
    metrics(y, b3_pred,         'B3: PERT × analytic S_i'),
    metrics(y, ml_full_pred,    'ML: XGBoost (CV)'),
])

b1_mae = results.loc[results['Model'].str.startswith('B1'), 'MAE'].values[0]
results['MAE improvement vs B1'] = results['MAE'].apply(
    lambda x: f"{((b1_mae - x) / b1_mae * 100):.1f}%"
)

print("\n─── Baseline comparison ───")
print(results.to_string(index=False))

# Bar plot of MAE
fig, ax = plt.subplots(figsize=(9, 5))
colors = ['#c0392b', '#e67e22', '#f1c40f', '#27ae60']
ax.bar(results['Model'], results['MAE'], color=colors)
ax.set_ylabel('MAE (days)')
ax.set_title('Baseline comparison: MAE by model tier')
ax.set_xticklabels(results['Model'], rotation=15, ha='right')
for i, row in results.iterrows():
    ax.text(i, row['MAE'] + 0.3, f"{row['MAE']}", ha='center', fontsize=9)
plt.tight_layout()
plt.savefig('baseline_comparison_xgb.png', dpi=150)
plt.close()
print("Saved: baseline_comparison_xgb.png")