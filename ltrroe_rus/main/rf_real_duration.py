"""
Модель случайного леса для предсказания детерминированной длительности проекта
на реальных метриках Gryzzly.
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

# 1. Загрузка данных
BASE_DIR = Path(__file__).resolve().parents[1]
FILES_DIR = BASE_DIR / "files"
VIS_DIR = BASE_DIR / "visual" / "rf_real_dur"
DATA_PATH = FILES_DIR / "metrics_results_full.csv"
VIS_DIR.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(DATA_PATH)

print("Размер датасета:", df.shape)

# 2. Признаки и целевая переменная
features = [
    'n_tasks', 'n_employees', 'n_dependencies', 
    'critical_path_tasks', 'avg_employee_efficiency'
]
X = df[features]
y = df['det_duration_days']

# 3. Разделение на обучающую и тестовую выборки 
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Обучающая выборка: {len(X_train)} задач")
print(f"Тестовая выборка: {len(X_test)} задач")

# 4. Обучение случайного леса 
model = RandomForestRegressor(
    n_estimators=300,
    max_depth=15,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)
print("Обучение случайного леса...")
model.fit(X_train, y_train)

# 5. Предсказание и оценка 
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\nРезультаты случайного леса (тестовая выборка):")
print(f"  MAE : {mae:.2f} дней")
print(f"  RMSE: {rmse:.2f} дней")
print(f"  R²  : {r2:.3f}")

# 6. Важность признаков 
importances = pd.Series(model.feature_importances_, index=features)
importances = importances.sort_values(ascending=False)
print("\nВажность признаков:")
print(importances.round(4))

# 7. Сохранение модели
MODEL_PATH = FILES_DIR / 'ltrroe_randomforest_model_real_duration.pkl'
joblib.dump(model, MODEL_PATH)
print(f"\nМодель сохранена в файл: {MODEL_PATH}")

# 8. Сохранение графиков
# 8.1 Диаграмма рассеяния: факт vs предсказание
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Фактическая длительность, дней')
plt.ylabel('Предсказанная длительность, дней')
plt.title('Факт vs Предсказание (Случайный лес)')
plt.savefig(VIS_DIR / 'actual_vs_predicted_rf.png')
plt.close()

# 8.2 Распределение ошибок
errors = y_test - y_pred
plt.figure(figsize=(10, 6))
sns.histplot(errors, bins=50, kde=True)
plt.xlabel('Ошибка, дней')
plt.title('Распределение ошибок (Случайный лес)')
plt.savefig(VIS_DIR / 'error_distribution_rf.png')
plt.close()

# 8.3 Столбчатая диаграмма важности признаков
plt.figure(figsize=(10, 6))
ax = importances.plot(kind='bar')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')  # поворот на 45°
plt.title('Важность признаков (Случайный лес)')
plt.ylabel('Вклад')
plt.tight_layout()
plt.savefig(VIS_DIR / 'feature_importance_rf.png')
plt.close()
