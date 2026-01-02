# Voter ID Laws & Welfare Benefits for Illegal Immigrants

Analysis and visualization of the relationship between state voter ID requirements and welfare benefit availability for illegal immigrants.

## Key Finding

States with no effective voter ID requirement offer **7.7x more welfare benefits** on average compared to states requiring ID verification (1.7 vs 0.2 out of 4).

| Category | No Effective ID (24 states) | ID Required (27 states) |
|----------|----------------------------|------------------------|
| Healthcare | 33% | 0% |
| Food Assistance | 21% | 0% |
| Cash Assistance | 71% | 22% |
| EITC (Tax Credit) | 46% | 0% |

## Methodology

Voter ID laws are categorized into five tiers by NCSL:

1. **Strict Photo ID** – Must show government-issued photo ID
2. **Strict Non-Photo ID** – Must show ID (photo not required)
3. **Non-Strict Photo ID** – Photo ID requested, alternatives allowed
4. **Non-Strict Non-Photo ID** – ID requested, can sign affidavit instead
5. **No Document Required** – Identity verified via signature match, etc.

For analysis, these are collapsed into two groups based on **functional outcome**:
- **ID Verification Required** (tiers 1-3): Voter must present a document
- **No Effective ID Requirement** (tiers 4-5): Voter can cast ballot without presenting ID

This grouping reflects whether voters can effectively vote without showing identification, regardless of what the law nominally requires.

## Visualizations

Three versions of the US map are provided:

- **5-tier** (`state_map.png`): Full NCSL classification
- **3-tier** (`state_map_3tier.png`): Strict / Non-Strict / Weak-None
- **2-tier** (`state_map_2tier.png`): ID Required vs No Effective ID (primary analysis)

## Data Sources

- **Voter ID Requirements**: National Conference of State Legislatures (NCSL)
- **Welfare Benefits**: National Immigration Law Center (NILC) state policy maps (2023-2024)

## Usage

### Requirements

```bash
pip install -r requirements.txt
```

### Generate Visualizations

```bash
cd src
python main.py
```

Output files will be created in the `output/` directory.

### Project Structure

```
├── data/
│   └── state_policies.csv    # State-level policy data
├── src/
│   ├── prepare_data.py       # Data loading and preparation
│   ├── stats.py              # Statistical analysis
│   ├── visualize.py          # Visualization functions
│   └── main.py               # Main pipeline
├── output/
│   ├── state_map.png         # 5-tier map
│   ├── state_map_3tier.png   # 3-tier map
│   ├── state_map_2tier.png   # 2-tier map
│   ├── comparison_chart.png  # Bar chart comparison
│   ├── strip_plot.html       # Interactive strip plot
│   └── choropleth_map.html   # Interactive choropleth
└── requirements.txt
```

## License

MIT
