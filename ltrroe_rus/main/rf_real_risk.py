"""
Модель случайного леса для предсказания длительности задачи.
Включает сравнение с бейзлайнами (PERT, PERT×средний slowdown, PERT×аналитический S_i).
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_predict
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Загрузка данных
DATA_PATH = '/Users/roryqwork/Documents/GitHub/LTRROE/metrics_results_full.csv'
df = pd.read_csv(DATA_PATH)

print("Размер датасета:", df.shape)

# 2. Признаки и целевая переменная
features = [
    'n_tasks', 'n_employees', 'n_dependencies', 
    'critical_path_tasks', 'avg_employee_efficiency'
]
X = df[features]
y = df['schedule_risk_ratio']

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
MODEL_PATH = 'ltrroe_randomforest_model_real.pkl'
joblib.dump(model, MODEL_PATH)
print(f"\nМодель сохранена в файл: {MODEL_PATH}")

# 8. Сохранение графиков
# 8.1 Диаграмма рассеяния: факт vs предсказание
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Фактический риск')
plt.ylabel('Предсказанный риск')
plt.title('Факт vs Предсказание (Случайный лес)')
plt.savefig('actual_vs_predicted_rf.png')
plt.close()

# 8.2 Распределение ошибок
errors = y_test - y_pred
plt.figure(figsize=(10, 6))
sns.histplot(errors, bins=50, kde=True)
plt.xlabel('Ошибка')
plt.title('Распределение ошибок (Случайный лес)')
plt.savefig('error_distribution_rf.png')
plt.close()

# 8.3 Столбчатая диаграмма важности признаков
plt.figure(figsize=(10, 6))
ax = importances.plot(kind='bar')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')  # поворот на 45°
plt.title('Важность признаков (Случайный лес)')
plt.ylabel('Вклад')
plt.tight_layout()
plt.savefig('feature_importance_rf.png')
plt.close()