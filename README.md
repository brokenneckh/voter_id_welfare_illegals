# Voter ID & Welfare Benefits — Replication Pipeline

Code + data for reproducing the project's empirical pipeline (analysis scripts, results, and paper artifacts).

## Repo layout

- **Pipeline / analysis code**: `src/` (entrypoint: `python src/main.py`)
- **Inputs + curated datasets**: `data/`
- **Figures**: `output/*.png`, `output/*.svg`, `output/*.html`
- **Statistical summary**: `output/summary_narrative.txt`

## Quick start

```bash
pip install -r requirements.txt
python src/main.py
```

This runs the complete 4-step pipeline and generates all 27 output files.

## Tests

```bash
pytest -q
```

---

# Part 2: High-Contrast Maps

The pipeline includes a high-contrast map generator (`src/high_contrast_maps.py`) that produces visualizations showing correlations between state policies and electoral outcomes.

## How It Works

The high-contrast maps module runs as **Step 4** of the main pipeline. It:

1. **Loads geographic data** from Census Bureau shapefiles (with local GeoJSON fallback)
2. **Merges policy data** from `data/state_policies.csv` (voter ID strictness, welfare benefits)
3. **Merges electoral data** from `data/panel_presidential_did.csv` (2024 presidential results)
4. **Generates three-panel comparison maps** showing:
   - Policy indicator map (left)
   - Electoral outcome map (right)
   - Alignment/match map (bottom)

## Color Scheme

All policy maps use a **2-tier blue color scheme** for consistency:

| Policy Status | Color | Hex |
|---------------|-------|-----|
| ID Required / Has Benefits | Dark Blue | `#084594` |
| No ID / No Benefits | Light Blue | `#deebf7` |

Electoral maps use traditional colors:
- Harris Won: Blue (`#0047ab`)
- Trump Won: Red (`#c41230`)

Alignment maps:
- Match: Green (`#2ca02c`)
- Mismatch: Orange (`#ff7f0e`)

## Output Files (12 figures)

### State-Level Maps (7 files)

| File | Description |
|------|-------------|
| `high_contrast_maps_2024.png` | Voter ID laws vs 2024 presidential (red/blue) |
| `high_contrast_maps_2tier_2024.png` | Voter ID laws vs 2024 presidential (2-tier blue) |
| `welfare_high_contrast_maps_2024.png` | Welfare benefits vs 2024 presidential |
| `unauthorized_pop_high_contrast_maps_2024.png` | Unauthorized immigrant population vs 2024 presidential |
| `combined_voter_id_welfare_2024.png` | 4-panel: both policies side-by-side |
| `voter_id_alignment_only_2024.png` | Single alignment map for voter ID |
| `welfare_alignment_only_2024.png` | Single alignment map for welfare |

### Border County Maps (2 files)

| File | Description |
|------|-------------|
| `border_counties_voter_id_2024.png` | County-level map highlighting voter ID policy borders |
| `border_counties_welfare_2024.png` | County-level map highlighting welfare policy borders |

These maps use Census county adjacency data to identify counties along state borders where policies differ.

### Correlation Bar Charts (3 files)

| File | Description |
|------|-------------|
| `state_presidential_correlation.png` | State-level gaps in Democratic vote share (Presidential 2024) |
| `state_house_correlation.png` | State-level gaps in Democratic vote share (US House 2024) |
| `border_correlation.png` | Border county gaps for both policies |

## Data Sources

| File | Description |
|------|-------------|
| `data/state_policies.csv` | Voter ID strictness (1-5 scale) and welfare benefit flags |
| `data/panel_presidential_did.csv` | State-level presidential vote shares by year |
| `data/county_presidential_2000_2020.csv` | County-level presidential results |
| `data/census_county_adjacency.csv` | Census Bureau county adjacency pairs |
| `data/border_links.csv` | Pre-computed welfare policy border county pairs |
| `data/unauthorized_immigrant_pop_2023.csv` | State unauthorized immigrant population estimates |
| `data/us_states.geojson` | State boundary geometries (fallback) |

## Running Standalone

The high-contrast maps module can be run independently:

```bash
python src/high_contrast_maps.py
```

This generates all 12 map figures in `output/`.

## Contributor notes

See `CLAUDE.md` for repo-specific conventions.

## License

MIT
