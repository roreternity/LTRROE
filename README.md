# LTRROE v2.0 — Local Team Resource & Risk Optimization Engine

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](../LICENSE)

**Stochastic modeling system for project risk assessment and resource optimization.**

## Quick Start

```bash
# Clone repository
git clone https://github.com/roreternity/LTRROE.git
cd LTRROE/ENG

# Install dependencies
pip install -r requirements.txt

# Run demonstration
python demo_ltrroe.py
```

Features

    Monte Carlo simulation - Probabilistic project scheduling

    Critical Path Method - Network analysis with resource constraints

    Human factor modeling - Skill-based performance assessment

    Comprehensive visualization - Four analytical report types

Project Structure
```
ENG/
├── models.py              # Data models (Project, Task, Employee)
├── algorithmes.py         # Core algorithms (CPM, Monte Carlo)
├── visualisation.py       # Visualization module (4 chart types)
├── test_data.py           # Test project generator
├── demo_ltrroe.py         # Complete demonstration script
└── requirements.txt       # Python dependencies
```
Core API Examples
```python
from test_data import create_test_project
from algorithmes import calculate_schedule, monte_carlo_simulation
from visualisation import plot_gantt_chart

# Create project and calculate schedule
project = create_test_project()
early_start, early_finish, _ = calculate_schedule(project)

# Risk analysis
durations = monte_carlo_simulation(project, num_simulations=1000)
print(f"Average duration: {sum(durations)/len(durations):.1f} days")

# Generate Gantt chart
plot_gantt_chart(project, early_start, early_finish)
```

Generated Reports

    gantt_chart.png - Schedule visualization with critical path

    monte_carlo_histogram.png - Probability distribution

    employee_load_heatmap.png - Resource utilization

    skills_radar_chart.png - Competency analysis

Academic Research

For academic context and research methodology, see README_ACADEMIC.md.
License

MIT License. See LICENSE for details.
Contact

Author: roreternity
GitHub: https://github.com/roreternity

Project: https://github.com/roreternity/LTRROE
