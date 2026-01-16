# High-Contrast Map Module

Self-contained module for generating high-contrast map figures showing the correlation between state policies, demographics, and electoral outcomes.

## Output Figures

This module generates four visualization figures:

1. **high_contrast_maps_2024.png** - Voter ID requirements vs presidential election results
2. **welfare_high_contrast_maps_2024.png** - Immigrant welfare benefits vs presidential election results
3. **unauthorized_pop_high_contrast_maps_2024.png** - Unauthorized immigrant population (absolute) vs presidential election results
4. **unauthorized_pop_pct_high_contrast_maps_2024.png** - Unauthorized immigrant population (% of state) vs presidential election results

Each figure contains three maps:
- Top-left: Policy/demographic distribution
- Top-right: Presidential election winner
- Bottom-center: Alignment between policy and voting patterns

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Generate all figures (2024 data)
python generate_maps.py
```

## Data Files

| File | Description |
|------|-------------|
| `state_policies.csv` | Voter ID strictness and welfare benefit indicators by state |
| `panel_presidential_did.csv` | Presidential election results (dem_share) by state and year |
| `unauthorized_immigrant_pop_2023.csv` | Unauthorized immigrant population by state (2023 estimates) |
| `us_states.geojson` | US state boundary geometries |
| `state_population_historical.csv` | State population by year (for % calculations) |

## Requirements

- Python 3.9+
- pandas >= 2.0
- geopandas >= 0.14
- matplotlib >= 3.7
- numpy >= 1.24

## Directory Structure

```
standalone_high_contrast_maps/
├── data/
│   ├── state_policies.csv
│   ├── panel_presidential_did.csv
│   ├── unauthorized_immigrant_pop_2023.csv
│   ├── us_states.geojson
│   └── state_population_historical.csv
├── output/
│   └── (generated figures)
├── generate_maps.py
├── requirements.txt
└── README.md
```
