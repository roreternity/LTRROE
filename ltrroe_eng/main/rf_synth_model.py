"""
Random Forest models on synthetic project-level metrics.

One CSV row represents one project. The script evaluates three project-level targets:
1) central project duration;
2) absolute tail width P90-P50;
3) relative tail width, Schedule Risk Ratio = (P90 - P50) / P50.

Several RF profiles are compared for each target. Model selection is based
on cross-validation inside the training split; final metrics are computed on the holdout split.
"""

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split


RANDOM_STATE = 42
BASE_DIR = Path(__file__).resolve().parents[1]
FILES_DIR = BASE_DIR / "files"
VIS_DIR = BASE_DIR / "visual" / "rf_synth_project"
DATA_PATH = FILES_DIR / "synthetic_project_metrics.csv"

FEATURES = [
    "n_tasks",
    "n_employees",
    "n_dependencies",
    "critical_path_tasks",
    "avg_employee_efficiency",
]

TARGETS = [
    ("det_duration_days", "project duration", "days", "duration"),
    ("p90_minus_p50", "absolute tail width P90-P50", "days", "tail_width"),
    ("schedule_risk_ratio", "Schedule Risk Ratio", "fraction", "risk_ratio"),
]

RF_PROFILES = [
    (
        "RF deep",
        {
            "n_estimators": 300,
            "max_depth": 15,
            "min_samples_split": 5,
        },
    ),
    (
        "RF mid",
        {
            "n_estimators": 300,
            "max_depth": 6,
            "min_samples_leaf": 5,
        },
    ),
    (
        "RF regularized",
        {
            "n_estimators": 300,
            "max_depth": 3,
            "min_samples_leaf": 5,
        },
    ),
]


def bool_series(series: pd.Series) -> pd.Series:
    """Robustly convert a CSV True/False column to bool."""
    if series.dtype == bool:
        return series
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def make_rf(params: dict) -> RandomForestRegressor:
    return RandomForestRegressor(
        **params,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )


def metrics_row(model_name: str, y_train, train_pred, y_test, test_pred, cv_scores=None) -> dict:
    row = {
        "model": model_name,
        "train_R2": r2_score(y_train, train_pred),
        "test_MAE": mean_absolute_error(y_test, test_pred),
        "test_RMSE": np.sqrt(mean_squared_error(y_test, test_pred)),
        "test_R2": r2_score(y_test, test_pred),
    }
    if cv_scores is not None:
        row["cv_R2_mean"] = cv_scores.mean()
        row["cv_R2_std"] = cv_scores.std()
    else:
        row["cv_R2_mean"] = np.nan
        row["cv_R2_std"] = np.nan
    return row


def train_target(df: pd.DataFrame, target_col: str, target_label: str, unit: str, slug: str) -> dict:
    X = df[FEATURES]
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    print(f"\n─── Target: {target_label} ───")
    print(f"Mean value:  {y.mean():.3f} {unit}")
    print(f"Median:           {y.median():.3f} {unit}")
    print(f"Training sample: {len(X_train)} projects")
    print(f"Test sample:  {len(X_test)} projects")

    rows = []

    dummy = DummyRegressor(strategy="mean")
    dummy.fit(X_train, y_train)
    rows.append(
        metrics_row(
            "Dummy mean",
            y_train,
            dummy.predict(X_train),
            y_test,
            dummy.predict(X_test),
        )
    )

    fitted_models = {}
    for profile_name, params in RF_PROFILES:
        print(f"Training {profile_name}...")
        cv_scores = cross_val_score(
            make_rf(params),
            X_train,
            y_train,
            cv=cv,
            scoring="r2",
            n_jobs=1,
        )
        model = make_rf(params)
        model.fit(X_train, y_train)
        fitted_models[profile_name] = model
        rows.append(
            metrics_row(
                profile_name,
                y_train,
                model.predict(X_train),
                y_test,
                model.predict(X_test),
                cv_scores=cv_scores,
            )
        )

    results = pd.DataFrame(rows)
    print("\nModel comparison:")
    print(
        results.round(
            {
                "cv_R2_mean": 3,
                "cv_R2_std": 3,
                "train_R2": 3,
                "test_MAE": 3,
                "test_RMSE": 3,
                "test_R2": 3,
            }
        ).to_string(index=False)
    )

    rf_results = results[results["model"] != "Dummy mean"]
    selected_name = rf_results.sort_values("cv_R2_mean", ascending=False).iloc[0]["model"]
    selected_model = fitted_models[selected_name]
    selected_pred = selected_model.predict(X_test)
    selected_row = results[results["model"] == selected_name].iloc[0].to_dict()

    print(f"\nSelected model by CV: {selected_name}")
    print(f"  MAE : {selected_row['test_MAE']:.3f} {unit}")
    print(f"  RMSE: {selected_row['test_RMSE']:.3f} {unit}")
    print(f"  R²  : {selected_row['test_R2']:.3f}")
    print(f"  train R²: {selected_row['train_R2']:.3f}")
    print(f"  CV R²: {selected_row['cv_R2_mean']:.3f} ± {selected_row['cv_R2_std']:.3f}")

    importances = pd.Series(selected_model.feature_importances_, index=FEATURES).sort_values(ascending=False)
    print("\nFeature importance for the selected model:")
    print(importances.round(4))

    model_path = FILES_DIR / f"rf_synth_project_{slug}.pkl"
    joblib.dump(selected_model, model_path)
    print(f"Model saved: {model_path}")

    save_plots(y_test, selected_pred, importances, target_label, unit, slug)

    return {
        "target": target_col,
        "selected_model": selected_name,
        "MAE": selected_row["test_MAE"],
        "RMSE": selected_row["test_RMSE"],
        "R2": selected_row["test_R2"],
        "train_R2": selected_row["train_R2"],
        "cv_R2": selected_row["cv_R2_mean"],
    }


def save_plots(
    y_test: pd.Series,
    y_pred: np.ndarray,
    importances: pd.Series,
    target_label: str,
    unit: str,
    slug: str,
) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(y_test, y_pred, alpha=0.55)
    low = min(y_test.min(), y_pred.min())
    high = max(y_test.max(), y_pred.max())
    ax.plot([low, high], [low, high], "r--", lw=2)
    ax.set_xlabel(f"Actual value ({unit})")
    ax.set_ylabel(f"Predicted value ({unit})")
    ax.set_title(f"Actual vs predicted: {target_label}")
    fig.tight_layout()
    fig.savefig(VIS_DIR / f"{slug}_actual_vs_predicted_rf.png", dpi=150)
    plt.close(fig)

    errors = y_test - y_pred
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(errors, bins=50, kde=True, ax=ax)
    ax.set_xlabel(f"Error ({unit})")
    ax.set_title(f"Error distribution: {target_label}")
    fig.tight_layout()
    fig.savefig(VIS_DIR / f"{slug}_error_distribution_rf.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6))
    importances.sort_values().plot(kind="barh", ax=ax)
    ax.set_xlabel("Contribution")
    ax.set_title(f"Feature importance: {target_label}")
    fig.tight_layout()
    fig.savefig(VIS_DIR / f"{slug}_feature_importance_rf.png", dpi=150)
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    print("File:", DATA_PATH)
    print("Dataset size before cleaning:", df.shape)

    df["p90_minus_p50"] = df["p90"] - df["p50"]

    if "mc_success" in df.columns:
        df = df[bool_series(df["mc_success"])].copy()

    required_cols = FEATURES + [target for target, *_ in TARGETS]
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=required_cols)

    print("Dataset size after cleaning:", df.shape)
    print("Observation unit: project")

    results = [train_target(df, *target_spec) for target_spec in TARGETS]
    results_df = pd.DataFrame(results)

    print("\n─── Selected-model summary ───")
    print(
        results_df.round(
            {
                "MAE": 3,
                "RMSE": 3,
                "R2": 3,
                "train_R2": 3,
                "cv_R2": 3,
            }
        ).to_string(index=False)
    )
    print(f"\nPlots saved to: {VIS_DIR}")


if __name__ == "__main__":
    main()
