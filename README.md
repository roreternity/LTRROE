# LTRROE

**LTRROE** (Local Team Resource & Risk Optimization Engine) is a research prototype for
stochastic project schedule-risk modelling. It combines CPM-style graph scheduling, Monte
Carlo simulation, synthetic data generation, and machine-learning baselines to compare a
*central* schedule estimate against the *upper tail* of the schedule distribution.

> 🇷🇺 Russian version of this document: [README.ru.md](README.ru.md)

## The idea

Deterministic CPM gives one number. That number is close to the **central scenario**, not a
safe deadline. LTRROE instead treats the project duration as a distribution and evaluates:

- `det_duration_days` / `P50` — the central outcome (CPM ≈ P50, provable via the CLT);
- `P90` — a cautious outcome;
- `Schedule Risk Ratio = (P90 − P50) / P50` — the relative size of the risk buffer.

**Key result (synthetic, 10 000 projects):** the project *duration* is predictable from
aggregate features (R² ≈ 0.78), but the *relative reserve* is not (R² ≈ 0.08). That gap is
the "boundary of predictability" — a fixed percentage buffer is not justified; each project
needs its own stochastic analysis.

## Repository layout

```text
ltrroe/
├── ltrroe/                 # the package
│   ├── paths.py            # single source of truth for all data/output paths
│   ├── core/               # language-independent engine
│   │   ├── objects.py      # Project, Task, Employee, Dependency
│   │   ├── algorithms.py   # CPM forward/backward pass, Monte Carlo
│   │   ├── visualisation.py
│   │   ├── test_data.py    # built-in demo project
│   │   └── demo.py         # runnable demo
│   └── synth/              # synthetic experiments
│       ├── project_level.py  # generate project-level dataset
│       ├── task_level.py     # generate task-level dataset
│       ├── rf_project.py     # RF: duration + risk ratio (project level)
│       ├── rf_task.py        # RF: task duration
│       ├── xgb_model.py      # XGBoost baseline
│       └── spearman.py       # sensitivity / correlation
├── tests/                  # pytest suite
├── outputs/                # generated CSVs, models, figures (gitignored)
├── data/                   # raw input data if any (gitignored)
├── pyproject.toml
├── Makefile
└── README.md / README.ru.md
```

## Quick start

```bash
make install     # pip install -e ".[dev,xgboost]"
make test        # run the test suite
make demo        # run the demo on the built-in test project
make all         # dataset -> ml -> figures
```

Or run a stage directly:

```bash
python -m ltrroe.synth.project_level   # generate the project-level dataset
python -m ltrroe.synth.rf_project      # train the project-level Random Forest
```

All generated artifacts go to `outputs/` (`outputs/files` for CSV/PKL, `outputs/figures`
for PNG) — configured centrally in `ltrroe/paths.py`.

## Note on the Gryzzly dataset

An earlier version validated against the public Gryzzly time-tracking dataset. It was
**excluded** because that dataset lacks the fields the model depends on (`task_skills` is
empty, so the skill-slowdown factor is disabled, and employee load never crosses the
threshold). The current pipeline is synthetic-only; Gryzzly is retained only as a documented
negative experiment, not as validation.

## Dependencies

Python 3.9+, `numpy`, `pandas`, `matplotlib`, `seaborn`, `scipy`, `scikit-learn`, `joblib`
(and optionally `xgboost`). Install via `make install`.

## License

MIT — see [LICENSE](LICENSE).
