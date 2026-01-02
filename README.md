# Voter ID Laws & Welfare Benefits for Illegal Immigrants

Analysis and visualization of the relationship between state voter ID requirements and state-funded welfare benefits **specifically available to illegal immigrants**.

## Key Finding

States with no effective voter ID requirement offer **7.7x more welfare benefits to illegal immigrants** on average compared to states requiring ID verification (1.7 vs 0.2 out of 4).

| Benefit Category | No Effective ID (24 states) | ID Required (27 states) |
|------------------|----------------------------|------------------------|
| **Any benefit for illegal immigrants** | **83%** | **22%** |
| Healthcare for illegal immigrants | 33% | **0%** |
| Food assistance for illegal immigrants | 21% | **0%** |
| Cash assistance for illegal immigrants | 71% | 22% |
| EITC for illegal immigrants (ITIN filers) | 46% | **0%** |

**Note:** Not a single state requiring ID verification offers healthcare (vs 33% of no-ID states), food assistance (vs 21%), or EITC (vs 46%) to illegal immigrants. The only overlap is cash assistance.

## What This Data Represents

The welfare benefits tracked here are **state-funded programs that extend eligibility to illegal immigrants**:

- **Healthcare**: State-funded health coverage for undocumented adults (federal Medicaid excludes them)
- **Food Assistance**: State-funded food programs beyond federal SNAP (which excludes undocumented immigrants)
- **Cash Assistance**: State-funded cash aid programs that include undocumented immigrants
- **EITC**: State Earned Income Tax Credit available to **ITIN filers** (Individual Taxpayer Identification Numbers are used by people who cannot obtain a Social Security Number, including undocumented immigrants)

A state with welfare score 0 doesn't mean it has no welfare programs—it means the state follows federal rules that exclude illegal immigrants from benefits. A state with score 4 has created state-funded alternatives that include them.

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

Map legend:
- **H** = Healthcare for illegal immigrants
- **F** = Food assistance for illegal immigrants
- **C** = Cash assistance for illegal immigrants
- **E** = EITC for illegal immigrants (ITIN filers)

## Data Sources

- **Voter ID Requirements**: National Conference of State Legislatures (NCSL)
- **Welfare Benefits for Illegal Immigrants**: National Immigration Law Center (NILC) state policy maps (2023-2024)

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
