# LTRROE Project Repository

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**LTRROE v2.0 — Local Team Resource & Risk Optimization Engine**  
*Research project in stochastic project risk modeling*

---

## Repository Structure

```
LTRROE/
├── ENG/                    # English version (full implementation)
│   ├── README.md          # Technical documentation (English)
│   ├── README_ACADEMIC_ENG.md # Academic research description (English)
│   ├── models.py          # Data models
│   ├── algorithmes.py     # Core algorithms
│   ├── visualisation.py   # Visualization module
│   ├── test_data.py       # Test data generator
│   └── demo_ltrroe.py     # Complete demonstration
│
├── RUS/                    # Russian version (for academic submission)
│   ├── README.md          # Техническая документация (русский)
│   ├── README_ACADEMIC_RUS.md  # Академическое описание (русский)
│   ├── models.py          # Модели данных
│   ├── algorithmes.py     # Основные алгоритмы
│   ├── visualisation.py   # Модуль визуализации
│   ├── test_data.py       # Генератор тестовых данных
│   └── demo_ltrroe.py     # Полная демонстрация
│
├── DOCS/                  # Documentation and research papers
│   ├── research_paper.pdf      # Academic paper (bilingual)
│   ├── presentation.pdf        # Research presentation
│   └── mathematical_model.pdf  # Formal model specification
│
├── EXAMPLES/              # Generated example outputs
│   ├── gantt_chart.png
│   ├── monte_carlo_histogram.png
│   ├── employee_load_heatmap.png
│   └── skills_radar_chart.png
│
├── LICENSE               # MIT License
└── README.md            # This file
```

---

## Quick Start

### For English Version:
```bash
cd ENG
pip install matplotlib numpy
python demo_ltrroe.py
```

### Для русской версии:
```bash
cd RUS
pip install matplotlib numpy
python demo_ltrroe.py
```

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

## Purpose

This repository contains **two complete implementations**:

1. **ENG/** - English version for international audience and GitHub
2. **RUS/** - Russian version for academic submissions to Russian universities

Both versions are functionally identical, differing only in language and documentation.

---

## Documentation

### Technical Documentation
- `ENG/README.md` - English technical documentation
- `RUS/README.md` - Русская техническая документация

### Academic Research Descriptions
- `ENG/README_ACADEMIC.md` - Academic context in English
- `RUS/README_АКАДЕМИЧЕСКИЙ.md` - Академическое описание на русском

### Formal Documentation
- `DOCS/research_paper.pdf` - Academic paper (bilingual)
- `DOCS/presentation.pdf` - Research presentation slides
- `DOCS/mathematical_model.pdf` - Formal mathematical model
- 
---

## Academic Submission

For submission to **HSE Faculty of Computer Science** (or other Russian universities):

1. **Submit from `RUS/` folder** (Russian version)
2. **Include `DOCS/research_paper.pdf`**
3. **Include `DOCS/presentation.pdf`**
4. **Provide GitHub repository link**

---

## Author

**roreternity**  
GitHub: [https://github.com/roreternity](https://github.com/roreternity)  
Repository: [https://github.com/roreternity/LTRROE](https://github.com/roreternity/LTRROE)

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

*Research project in stochastic optimization and project risk analysis.*  
*Developed for academic research applications.*
```
