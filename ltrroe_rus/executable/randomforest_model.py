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
DATA_PATH = '/Users/roryqwork/Documents/Workspace/LTRROE/ltrroe_rus/datasets/synthetic_tasks.csv'
df = pd.read_csv(DATA_PATH)

print("Размер датасета:", df.shape)
print("Средняя длительность задачи:", df['actual_duration'].mean().round(2), "дней")
print("Медианная длительность:", df['actual_duration'].median().round(2), "дней")

# 2. Признаки и целевая переменная
features = [
    'planned_optimistic', 'planned_likely', 'planned_pessimistic',
    'criticality', 'cost',
    'assigned_avg_efficiency', 'assigned_total_load',
    'num_predecessors', 'num_successors'
]
X = df[features]
y = df['actual_duration']

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
MODEL_PATH = 'ltrroe_randomforest_model.pkl'
joblib.dump(model, MODEL_PATH)
print(f"\nМодель сохранена в файл: {MODEL_PATH}")

# 8. Сохранение графиков
# 8.1 Диаграмма рассеяния: факт vs предсказание
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Фактическая длительность (дни)')
plt.ylabel('Предсказанная длительность (дни)')
plt.title('Факт vs Предсказание (Случайный лес)')
plt.savefig('actual_vs_predicted_rf.png')
plt.close()

# 8.2 Распределение ошибок
errors = y_test - y_pred
plt.figure(figsize=(10, 6))
sns.histplot(errors, bins=50, kde=True)
plt.xlabel('Ошибка (дни)')
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

# 9. Бейзлайны (на всём датасете)
# Бейзлайн B1: чистый PERT
pert_pred = (df['planned_optimistic'] + 4 * df['planned_likely'] + df['planned_pessimistic']) / 6

# Бейзлайн B2: PERT × средний slowdown
actual_slowdown = y / pert_pred
mean_slowdown = actual_slowdown.mean()
b2_pred = pert_pred * mean_slowdown

# Бейзлайн B3: PERT × аналитический slowdown из признаков primary
s_skill = np.where(
    df['primary_miss_ratio'] >= 1.0, 3.0,
    np.where(df['primary_miss_ratio'] > 0,
             2.0 + df['primary_miss_ratio'],
             1.0 / df['primary_min_efficiency'].clip(lower=0.1))
)
s_load = 1 + df['primary_overload'] * 0.05
b3_pred = pert_pred * s_skill * s_load

# ML на всём датасете через кросс-валидацию (без утечки)
ml_full_pred = cross_val_predict(
    RandomForestRegressor(n_estimators=300, max_depth=15, min_samples_split=5,
                          random_state=42, n_jobs=-1),
    X, y, cv=5
)

# ========================= 10. Сравнение моделей =========================
def metrics(y_true, y_pred, label):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return {'Модель': label, 'MAE': round(mae,2), 'RMSE': round(rmse,2), 'R²': round(r2,3)}

results = pd.DataFrame([
    metrics(y, pert_pred,       'B1: PERT (без учёта человека)'),
    metrics(y, b2_pred,         'B2: PERT × средний slowdown'),
    metrics(y, b3_pred,         'B3: PERT × аналитический S_i'),
    metrics(y, ml_full_pred,    'ML: Случайный лес (CV)'),
])

b1_mae = results.loc[results['Модель'].str.startswith('B1'), 'MAE'].values[0]
results['Улучшение MAE vs B1'] = results['MAE'].apply(
    lambda x: f"{((b1_mae - x) / b1_mae * 100):.1f}%"
)

print("\n─── Сравнение бейзлайнов ───")
print(results.to_string(index=False))

# Столбчатая диаграмма MAE
fig, ax = plt.subplots(figsize=(9, 5))
colors = ['#c0392b', '#e67e22', '#f1c40f', '#27ae60']
ax.bar(results['Модель'], results['MAE'], color=colors)
ax.set_ylabel('MAE (дни)')
ax.set_title('Сравнение бейзлайнов: MAE по уровню модели')
ax.set_xticklabels(results['Модель'], rotation=15, ha='right')
for i, row in results.iterrows():
    ax.text(i, row['MAE'] + 0.3, f"{row['MAE']}", ha='center', fontsize=9)
plt.tight_layout()
plt.savefig('baseline_comparison_rf.png', dpi=150)
plt.close()
print("Сохранено: baseline_comparison_rf.png")