# LTRROE Project Repository

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**LTRROE v2.0 — Local Team Resource & Risk Optimization Engine**  
*Research project in stochastic project risk modeling*

---

## Repository Structure

```
LTRROE/
├── ENG/                              # English version
│   ├── datasets/                     # Synthetic dataset (CSV)
│   ├── executable/                   # All Python source code
│   ├── models/                       # Trained ML models (.pkl)
│   └── visual/                       # Generated plots
│
├── RUS/                              # Russian version (same structure)
│   ├── datasets/                     # Synthetic dataset (CSV)
│   ├── executable/                   # Source code (Russian)
│   ├── models/                       # Trained ML models (.pkl)
│   └── visual/                       # Generated plots
│
├── LICENSE                           # MIT License
└── README.md                         # This file
```

> Both `ENG/` and `RUS/` are **functionally identical** – only the language differs.

---

## Project Overview

LTRROE is a stochastic modeling system for project risk assessment that implements:

- **Monte Carlo simulation** for probabilistic scheduling
- **Critical Path Method (CPM)** with resource constraints
- **Human factor modeling** based on skill efficiency
- **Comprehensive visualization** (4 analytical report types)

**Generated outputs:**
1. Gantt charts with critical path
2. Probability distributions of completion dates
3. Resource utilization heatmaps
4. Skills gap radar charts

---

## Quick Start

```bash
# Install dependencies
pip install numpy pandas matplotlib seaborn scikit-learn xgboost scipy

# Run English demo
cd ENG/executable
python demo_ltrroe.py

# Run Russian demo
cd RUS/executable
python demo_ltrroe.py
```

---

## Research Use

This project is designed for academic research in stochastic optimization and project risk analysis.  
Both language versions are provided for convenience.

---

## Author

**roreternity**  
GitHub: [https://github.com/roreternity](https://github.com/roreternity)  
Repository: [https://github.com/roreternity/LTRROE](https://github.com/roreternity/LTRROE)

---

## License

MIT License – see [LICENSE](LICENSE) file for details.

---

*Research project in stochastic optimization and project risk analysis.*  
*Developed for academic research applications.*
