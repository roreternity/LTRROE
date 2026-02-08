# LTRROE v2.0 — Local Team Resource & Risk Optimization Engine

Intelligent decision support system for project risk management using probabilistic models and visualization.

## Quick Start

### Installation
```bash
git clone https://github.com/roreternity/LTRROE.git
cd LTRROE
pip install matplotlib numpy
```

### Basic Usage
```python
from test_data import create_test_project
from algorithmes import calculate_schedule, monte_carlo_simulation
from visualisation import plot_gantt_chart

project = create_test_project()
early_start, early_finish, _ = calculate_schedule(project)
durations = monte_carlo_simulation(project, num_simulations=1000)
plot_gantt_chart(project, early_start, early_finish)
print(f"Average duration: {sum(durations)/len(durations):.1f} days")
```

## Features

### Project Planning
- Forward/Backward pass (CPM)
- Task dependency management
- Critical path identification

### Risk Analysis
- Monte Carlo simulation (1000+ iterations)
- Triangular distribution (PERT)
- Human factor modeling (skills, overload)

### Visualization
- Gantt charts with criticality coding
- Monte Carlo distribution histograms
- Skills radar charts
- Employee workload heatmaps

## Project Structure
```
LTRROE/
├── models.py              # Domain models
├── test_data.py           # Test data 
├── algorithmes.py         # Core algorithms
├── visualisation.py       # Visualization module
└── README.txt
```

## Example Output
```
Monte Carlo Simulation (1000 iterations):
Average: 37.2 days
Risk of missing 30-day deadline: 100.0%

Employee Load Analysis:
Alexey Seniorov: avg 12.5h/day - ⚠️ OVERLOAD
Maria Middlova: avg 6.1h/day - ✅ OK
```

## Core API
```python
# Schedule calculation
early_start, early_finish, task_duration = calculate_schedule(project)

# Risk analysis
durations = monte_carlo_simulation(project, num_simulations=1000)

# Visualization
plot_gantt_chart(project, early_start, early_finish)
plot_monte_carlo_histogram(durations, deadline=30)
plot_employee_load_heatmap(project, early_start, early_finish)
plot_skills_radar_chart(project)
```

## Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

## License
MIT License - see LICENSE file.

## Contact
Author: roreternity  
Project Link: https://github.com/roreternity/LTRROE
# LTRROE
