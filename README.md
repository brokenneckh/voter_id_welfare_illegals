# Voter ID Laws & Welfare Benefits for Illegal Immigrants

Analysis of the relationship between state voter ID requirements and state-funded welfare benefits available to illegal immigrants.

## Methodology Note

This analysis distinguishes between different immigrant populations rather than collapsing all into a single category:

| Column | Description |
|--------|-------------|
| `health_children` | State covers illegal immigrant children |
| `health_adults` | State covers ALL illegal immigrant adults (working age) |
| `health_seniors` | State covers illegal immigrant seniors 65+ only |
| `food` | State food assistance available to illegal immigrants |
| `eitc` | State EITC available to ITIN filers |

**Cash assistance was removed** from this analysis because research shows virtually no states provide direct cash to illegal immigrant working-age adults. Programs like California's CAPI serve legal immigrants only.

**Note on EITC for ITIN Filers:** State EITC programs that extend eligibility to ITIN filers primarily benefit illegal immigrants. According to the [Immigration Research Initiative](https://immresearch.org/publications/people-who-are-undocumented-occupations-taxes-paid-and-long-term-economic-benefits/), "the overwhelming majority of people filing taxes using ITINs are people who are undocumented, but there are some limited reasons others may also file this way." Other ITIN users include nonresident aliens with US tax obligations (foreign investors, student visa holders, spouses/dependents of work visa holders).

## Key Finding

States without effective voter ID requirements offer significantly more welfare benefits to illegal immigrants:

| Benefit Category | No Effective ID (24 states) | ID Required (27 states) |
|------------------|----------------------------|------------------------|
| Healthcare (adults) | 25% | **0%** |
| Healthcare (children) | 54% | 4% |
| Healthcare (seniors 65+) | 8% | **0%** |
| Food assistance | 21% | **0%** |
| EITC (ITIN filers) | 46% | **0%** |

**Note:** Not a single state requiring ID verification offers healthcare for illegal immigrant adults, food assistance, or EITC to illegal immigrants. The only overlap is children's healthcare (Rhode Island).

## What This Data Represents

The welfare benefits tracked here are **state-funded programs that extend eligibility to illegal immigrants**:

- **Healthcare (Adults)**: State-funded health coverage for illegal immigrant adults of all ages (CA, CO, MN, OR, WA, DC)
- **Healthcare (Children)**: State-funded health coverage for illegal immigrant children (14 states + DC)
- **Healthcare (Seniors)**: State covers illegal immigrant seniors 65+ only (IL, NY)
- **Food Assistance**: State-funded food programs beyond federal SNAP (CA, IL, ME, MN, WA)
- **EITC**: State Earned Income Tax Credit available to **ITIN filers** (11 states + DC)

A state with welfare score 0 doesn't mean it has no welfare programs—it means the state follows federal rules that exclude illegal immigrants from benefits.

## Program Usage Data

California publishes the most transparent enrollment data for these programs:

| Program | Enrollment | Annual Cost | Source |
|---------|------------|-------------|--------|
| Healthcare (Medi-Cal) | 1.7 million | $8.5 billion | [CalMatters](https://calmatters.org/health/2025/03/medi-cal-budget-shortfall/) |
| EITC (CalEITC) | ~315,000 ITIN filers | — | [PPIC](https://www.ppic.org/blog/are-eligible-undocumented-immigrants-claiming-the-caleitc-and-young-child-tax-credit/) |

**Other states with available data:**
- Washington: ~24,000 enrolled/applying for Medicaid expansion
- Colorado: 11,000 (hit enrollment cap in first 2 days)
- New York: 480,000 in emergency Medicaid (seniors 65+ only for full coverage)

Most states do not publish immigration-status breakdowns for program enrollment.

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

This grouping reflects whether voters can effectively vote without showing identification at the polling place.

## Welfare Scores

Two welfare scores are calculated:

1. **Adults Score (0-3)**: `health_adults + food + eitc`
   - Most defensible metric focused on working-age illegal immigrant adults

2. **Any Coverage Score (0-3)**: `(any health coverage) + food + eitc`
   - Broader metric including children and seniors

## Visualizations

- **5-tier map** (`state_map.png`): Full NCSL classification with benefit symbols
- **2-tier map** (`state_map_2tier.png`): ID Required vs No Effective ID (primary analysis)

Map legend:
- **Ha** = Healthcare for illegal immigrant adults
- **Hc** = Healthcare for illegal immigrant children
- **Hs** = Healthcare for illegal immigrant seniors (65+)
- **F** = Food assistance for illegal immigrants
- **E** = EITC for ITIN filers

## Data Sources

- **Voter ID Requirements**: National Conference of State Legislatures (NCSL)
- **Health Coverage**: KFF State Health Coverage for Immigrants (2024), NILC Health Coverage Maps
- **Food Assistance**: NILC State Food Programs Table
- **EITC for ITIN Filers**: ITEP State EITC Analysis (2024)

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
│   ├── state_map_2tier.png   # 2-tier map
│   ├── comparison_chart.png  # Bar chart comparison
│   ├── strip_plot.html       # Interactive strip plot
│   └── choropleth_map.html   # Interactive choropleth
└── requirements.txt
```

## License

MIT
