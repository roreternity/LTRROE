"""
Random Forest model for Schedule Risk Ratio prediction
on real Gryzzly metrics.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 1. Load data
BASE_DIR = Path(__file__).resolve().parents[1]
FILES_DIR = BASE_DIR / "files"
VIS_DIR = BASE_DIR / "visual" / "rf_real_risk"
DATA_PATH = FILES_DIR / "metrics_results_full.csv"
VIS_DIR.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(DATA_PATH)

print("Dataset size:", df.shape)

# 2. Features and target variable
features = [
    'n_tasks', 'n_employees', 'n_dependencies', 
    'critical_path_tasks', 'avg_employee_efficiency'
]
X = df[features]
y = df['schedule_risk_ratio']

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
MODEL_PATH = FILES_DIR / 'ltrroe_randomforest_model_real_risk.pkl'
joblib.dump(model, MODEL_PATH)
print(f"\nModel saved to: {MODEL_PATH}")

# 8. Save plots
# 8.1 Scatter plot: actual vs predicted
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Actual Schedule Risk Ratio')
plt.ylabel('Predicted Schedule Risk Ratio')
plt.title('Actual vs Predicted (Random Forest)')
plt.savefig(VIS_DIR / 'actual_vs_predicted_rf.png')
plt.close()

# 8.2 Error distribution
errors = y_test - y_pred
plt.figure(figsize=(10, 6))
sns.histplot(errors, bins=50, kde=True)
plt.xlabel('Error')
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
