# LTRROE

**LTRROE** (Local Team Resource & Risk Optimization Engine) is a research prototype for stochastic project schedule-risk modeling. The project combines CPM-style graph scheduling, Monte Carlo simulation, synthetic data generation, and machine-learning baselines for comparing central schedule estimates with upper-tail schedule risk.

The core research idea is simple: deterministic CPM can be close to the central scenario of a project, but it does not describe the width of the possible schedule distribution. LTRROE therefore evaluates both the central duration (`det_duration_days`, `P50`) and the upper-risk scenario (`P90`, `Schedule Risk Ratio = (P90 - P50) / P50`).

## Repository Layout

```text
LTRROE_3/
├── ltrroe_rus/
│   ├── main/                    # Russian source code and comments
│   ├── files/                   # Generated CSV metrics and trained models
│   ├── real_datasets_gryzzly/   # Local Gryzzly CSV files
│   └── visual/                  # Generated figures
├── ltrroe_eng/
│   ├── main/                    # Same code as ltrroe_rus, with English comments
│   ├── files/
│   ├── real_datasets_gryzzly/
│   └── visual/
├── LICENSE
└── README.md
```

`ltrroe_rus` and `ltrroe_eng` are intended to be functionally identical. The Russian version is convenient for the article draft; the English version keeps the same code and outputs, but uses English comments and script messages.

## Data

The real-data validation uses the public Gryzzly time-tracking dataset:

- Dataset DOI: <https://doi.org/10.6084/m9.figshare.28114247.v2>
- Data descriptor: Abitbol J. L., Arod L. *Seven years of time-tracking data capturing collaboration and failure dynamics: the Gryzzly dataset*. Scientific Data 12, 578 (2025). <https://doi.org/10.1038/s41597-025-04903-2>
- Original Gryzzly analysis repository: <https://github.com/jaklevab/gryzzly>

Expected local CSV files:

```text
real_datasets_gryzzly/
├── declarations.csv
├── projects.csv
├── projects_computed.csv
├── subscriptions.csv
├── tasks.csv
├── tasks_computed.csv
├── teams.csv
└── users.csv
```

## Main Scripts

Run scripts from the repository root or from the corresponding `main/` directory. Paths inside the scripts are resolved relative to their language folder.

```bash
# 1. Build LTRROE project objects from the Gryzzly CSV files
python ltrroe_rus/main/import_gryzzly_data.py

# 2. Run deterministic CPM and Monte Carlo metrics for real projects
python ltrroe_rus/main/run_simulations.py

# 3. Generate a synthetic project-level dataset comparable to real metrics
python ltrroe_rus/main/generate_synth_project_metrics.py

# 4. Train Random Forest models on synthetic project metrics
python ltrroe_rus/main/rf_synth_model.py

# 5. Train Random Forest models on real Gryzzly project metrics
python ltrroe_rus/main/rf_real_duration.py
python ltrroe_rus/main/rf_real_risk.py
```

Use `ltrroe_eng/main/...` for the English-commented mirror of the same pipeline.

## Generated Outputs

Important generated artifacts are stored under each language folder:

- `files/ltrroe_real_projects.pkl` — serialized LTRROE projects built from Gryzzly CSVs.
- `files/metrics_results_full.csv` — real project metrics after Monte Carlo simulation.
- `files/synthetic_project_metrics.csv` — synthetic project-level metrics.
- `files/*.pkl` — trained ML models.
- `visual/final/` — final real-data figures for the article.
- `visual/rf_synth_project/`, `visual/rf_real_dur/`, `visual/rf_real_risk/` — ML diagnostic figures.

## Python Dependencies

The project was developed with Python 3.8+ and uses:

```bash
pip install numpy pandas matplotlib seaborn scikit-learn scipy xgboost joblib
```

`xgboost` is only required for `xgb_synth_model.py`.

## Notes

- The real Gryzzly CSVs are large; if they are not present locally, download them from the dataset DOI above and place them in `ltrroe_rus/real_datasets_gryzzly/` and/or `ltrroe_eng/real_datasets_gryzzly/`.
- Monte Carlo scripts can take noticeable time. `run_simulations.py` currently uses `NUM_SIMULATIONS = 10000` for stable project-level percentiles.
- `avg_employee_efficiency` in the real-data pipeline is a proxy feature based on planned/elapsed ratios. It should not be interpreted as a direct measurement of individual productivity.

## License

MIT License. See [LICENSE](LICENSE).
